"""
Text Classification
"""

import pandas as pd
import numpy as np

def txt_to_num_representation(df, txtCol, __lang, returnTfiDf=None):
    """
    Sanitize text representation

    Text to Numbers and noise deletion
    
    sublinear_df is set to True to use a logarithmic form for frequency.

    min_df is the minimum numbers of documents a word must
    be present in to be kept.

    norm is set to l2, to ensure all our feature vectors have
    a euclidian norm of 1.

    ngram_range is set to (1, 2) to indicate that we want
    to consider both unigrams and bigrams.

    stop_words is set to "english" to remove all common
    pronouns ("a", "the", ...) to reduce the number of noisy features.
    """
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    tfidf = TfidfVectorizer(
        sublinear_tf=True, min_df=5,
        norm='l2', encoding='latin-1',
        ngram_range=(1,2), stop_words=__lang
    )
    
    features = tfidf.fit_transform(df[txtCol]).toarray()
    
    if returnTfiDf:
        return features, tfidf
    else:
        return features


def correlated_words(dataFile, refCol, dataCol, outTbl, lang='english', N=2, refSheet=None):
    """
    Get words correlated with some text class 
    """
    
    from sklearn.feature_selection import chi2
    from gasp3.to                  import obj_to_tbl
    from gasp3.fm                  import tbl_to_obj
    
    # Data to DataFrame
    trainDf = tbl_to_obj(dataFile, sheet=refSheet)
    
    # Just in case, delete rows with NULL refCol and NULL dataCol
    trainDf = trainDf[pd.notnull(trainDf[dataCol])]
    trainDf = trainDf[pd.notnull(trainDf[refCol])]
    
    """
    Add a column encoding the reference classes as an integer because
    categorical variables are often better represented by integers
    than strings
    """
    
    from io import StringIO
    
    # Get a ID for Ref/text classes values
    trainDf['ref_id'] = trainDf[refCol].factorize()[0]
    
    # Create Dataframe only with ref_id's, without duplicates
    ref_id_df = trainDf[[refCol, 'ref_id']].drop_duplicates().sort_values(
        'ref_id'
    )
    
    # Create dicts to easy relate ref_id with ref_value
    ref_to_id = dict(ref_id_df.values)
    id_to_ref = dict(ref_id_df[['ref_id', refCol]].values)
    
    """
    Text to numbers
    """
    features, tfidf = txt_to_num_representation(
        trainDf, dataCol, lang, returnTfiDf=True)
    
    labels = trainDf.ref_id
    
    """
    Get most correlated words
    """
    
    corr_words = []
    for ref_name, ref_id in sorted(ref_to_id.items()):
        features_chi2 = chi2(features, labels == ref_id)
        
        indices = np.argsort(features_chi2[0])
        
        feat_names = np.array(tfidf.get_feature_names())[indices]
        
        unigrams = [v for v in feat_names if len(v.split(' ')) == 1][-N:]
        bigrams  = [v for v in feat_names if len(v.split(' ')) == 2][-N:]
        cols_d = [ref_name] + unigrams + bigrams
        
        corr_words.append(cols_d)
    
    COLS_NAME = ['ref_name'] + [
        'unigram_{}'.format(str(i+1)) for i in range(N)
    ] + [
        'bigram_{}'.format(str(i+1)) for i in range(N)
    ]
    dfCorrWords = pd.DataFrame(corr_words,columns=COLS_NAME)
    
    return obj_to_tbl(dfCorrWords, outTbl)


def model_selection(dataFile, refCol, dataCol, outTbl, lang='english', CV=5):
    """
    See which model is better to use in text classification for a specific
    data sample
    
    Compare:
    Logistic Regression (LogisticRegression)
    (Multinomial) Naive Bayes (MultinomialNB)
    Linear Support Vector Machine (LinearSVC)
    Random Forest (RandomForestClassifier)
    """
    
    import os
    from gasp3.pyt.oss                   import get_filename
    from gasp3.fm                        import tbl_to_obj
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model            import LogisticRegression
    from sklearn.ensemble                import RandomForestClassifier
    from sklearn.svm                     import LinearSVC
    from sklearn.naive_bayes             import MultinomialNB
    from sklearn.model_selection         import cross_val_score
    from gasp3.to                        import obj_to_tbl
    
    # Data to DataFrame
    trainDf = tbl_to_obj(dataFile)
    
    # Just in case, delete rows with NULL refCol and NULL dataCol
    trainDf = trainDf[pd.notnull(trainDf[dataCol])]
    trainDf = trainDf[pd.notnull(trainDf[refCol])]
    
    # Ref col to integers
    from io import StringIO
    
    trainDf['ref_id'] = trainDf[refCol].factorize()[0]
    
    # Text to numbers
    features = txt_to_num_representation(trainDf, dataCol, lang)
    
    labels = trainDf.ref_id
    
    """ Test Models """
    models = [
        RandomForestClassifier(n_estimators=200, max_depth=3, random_state=0),
        LinearSVC(),
        MultinomialNB(),
        LogisticRegression(random_state=0)
    ]
    
    cv_df = pd.DataFrame(index=range(CV * len(models)))
    entries = []
    
    for model in models:
        m_name = model.__class__.__name__
        accuracies = cross_val_score(
            model, features, labels, scoring='accuracy', cv=CV
        )
        
        for fold_idx, accuracy in enumerate(accuracies):
            entries.append((m_name, fold_idx, accuracy))
    
    # Create and Export evaluation table
    cv_df = pd.DataFrame(
        entries, columns=['model_name', 'fold_idx', 'accuracy'])
    cv_df_gp = pd.DataFrame(cv_df.groupby('model_name').accuracy.mean())
    cv_df_gp.reset_index(inplace=True)
    
    # Export Graphic
    import seaborn as sns
        
    a = sns.boxplot(x='model_name', y='accuracy', data=cv_df)
        
    b = sns.stripplot(
        x='model_name', y='accuracy', data=cv_df,
        size=10, jitter=True, edgecolor="gray", linewidth=2)
        
    fig = b.get_figure()
    fig.savefig(os.path.join(
        os.path.dirname(outTbl), get_filename(outTbl) + '.png'
    ))
    
    return obj_to_tbl(cv_df_gp, outTbl)


def text_prediction(trainData, classData, trainRefCol, trainClsCol, clsDataCol,
                    outfile, method='NaiveBayes', lang='english'):
    """
    Text classification
    
    Naive Bayes Classifier: the one most suitable for
    word counts is the multinomial variant: MultinomialNB
    
    Classifier Options:
    1) NaiveBayes;
    2) LinearSupportVectorMachine;
    3) RandomForest;
    4) LogisticRegression.
    """
    
    import pandas as pd
    from gasp3.fm import tbl_to_obj
    from gasp3.to import obj_to_tbl
    
    # Data to Dataframe
    trainDf = tbl_to_obj(trainData)
    classDf = tbl_to_obj(classData)
    
    # Just in case, delete rows with NULL refCol and NULL dataCol
    trainDf = trainDf[pd.notnull(trainDf[trainClsCol])]
    trainDf = trainDf[pd.notnull(trainDf[trainRefCol])]
    classDf = classDf[pd.notnull(classDf[clsDataCol])]
    
    if method == 'NaiveBayes':
        from sklearn.naive_bayes             import MultinomialNB
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.feature_extraction.text import TfidfTransformer
        
        """" Train Model """
        # X train is trainClsCol
        # Y train is trainRefCol
        x_train, y_train = trainDf[trainClsCol], trainDf[trainRefCol]
    
        count_vect = CountVectorizer()
    
        X_train_counts = count_vect.fit_transform(x_train)
    
        tfidf_transformer = TfidfTransformer()
    
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    
        clf = MultinomialNB().fit(X_train_tfidf, y_train)
    
        """ Predict """
        result = clf.predict(count_vect.transform(classDf[clsDataCol]))
    
        classDf['classification'] = result
    
    elif method == 'LinearSupportVectorMachine':
        from sklearn.svm import LinearSVC
        
        # Get features and Labels
        trainDf['ref_id'] = trainDf[trainRefCol].factorize()[0]
        labels = trainDf.ref_id
        
        features, tvect = txt_to_num_representation(
            trainDf, trainClsCol, __lang=lang, returnTfiDf=True)
        
        featTst = tvect.transform(classDf[clsDataCol])
        
        """ Train model """
        model = LinearSVC()
        
        model.fit(features, labels)
        
        y_pred = model.predict(featTst)
        
        classDf['classification'] = y_pred
        
        # Create Dataframe only with ref_id's, without duplicates
        ref_id_df = trainDf[[
            trainRefCol, 'ref_id'
        ]].drop_duplicates().sort_values('ref_id')
        ref_id_df.columns = ['class_name', 'ref_fid']
        
        classDf = classDf.merge(
            ref_id_df, how='inner',
            left_on='classification', right_on='ref_fid'
        )
        
        classDf.drop(['ref_fid'], axis=1, inplace=True)
    
    elif method == 'RandomForest':
        from sklearn.ensemble import RandomForestClassifier
        # Get features
        
        features, tvect = txt_to_num_representation(
            trainDf, trainClsCol, __lang=lang, returnTfiDf=True)
        
        featTst = tvect.transform(classDf[clsDataCol])
        
        classifier = RandomForestClassifier(
            n_estimators=1000, random_state=0
        )
        classifier.fit(features, trainDf[trainRefCol])
        
        y_pred = classifier.predict(featTst)
        
        classDf['classification'] = y_pred
    
    elif method == 'LogisticRegression':
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.feature_extraction.text import TfidfTransformer
        from sklearn.pipeline                import Pipeline
        from sklearn.linear_model            import LogisticRegression
        
        logreg = Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', LogisticRegression(n_jobs=1, C=1e5, multi_class='auto', solver='lbfgs')),
        ])
        
        logreg.fit(trainDf[trainClsCol], trainDf[trainRefCol])
        
        y_pred = logreg.predict(classDf[clsDataCol])
        
        classDf['classification'] = y_pred
    
    return obj_to_tbl(classDf, outfile)


def model_evaluation(tblFile, refCol, clsCol, outMxt):
    """
    Model Evaluation
    """
    
    import pandas as pd
    from gasp3.fm import tbl_to_obj
    from gasp3.to import obj_to_tbl
    from sklearn.metrics import confusion_matrix, classification_report
    
    data = tbl_to_obj(tblFile)
    
    ref_id = data[[refCol]].drop_duplicates().sort_values(refCol)
    print(data)
    
    conf_mat = confusion_matrix(data[refCol], data[clsCol])
    
    mxt = pd.DataFrame(
        conf_mat, columns=ref_id[refCol].values, index=ref_id[refCol].values)
    mxt.reset_index(inplace=True)
    mxt.rename(columns={'index' : 'confusion_mxt'}, inplace=True)
    
    # Get classification report
    report = classification_report(
        data[refCol], data[clsCol],
        target_names=ref_id[refCol],
        output_dict=True
    )
    
    global_keys = ['accuracy', 'macro avg', 'micro avg', 'weighted avg']
    
    cls_eval = {k : report[k] for k in report if k not in global_keys}
    glb_eval = {k : report[k] for k in report if k in global_keys}
    
    if 'accuracy' in glb_eval:
        glb_eval['accuracy'] = {
            'f1-score' : glb_eval['accuracy'], 'precision' : 0,
            'recall' : 0, 'support' : 0
        }
    
    cls_eval = pd.DataFrame(cls_eval).T
    gbl_eval = pd.DataFrame(glb_eval).T
    
    return obj_to_tbl([gbl_eval, cls_eval, mxt], outMxt, sheetsName=['global', 'report', 'matrix'])

