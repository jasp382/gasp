Install GASP Dependencies in CentOS 7
====================

### 1 - Install software needed to compile GDAL and GRASS GIS: ###

	sudo yum -y install epel-release
	sudo yum -y groupinstall "Development Tools"
	sudo yum -y install flex bison make zlib-devel gcc-c++ gettext sqlite-devel mesa-libGL-devel mesa-libGLU-devel libXmu-devel libX11-devel fftw-devel libtiff-devel lesstif-devel python-devel numpy wxPython wxGTK-devel proj proj-devel proj-epsg proj-nad libxml2 libxml2-devel geos geos-devel netcdf netcdf-devel blas-devel lapack-devel atlas-devel python-dateutil python-imaging python-matplotlib python-sphinx python-pip doxygen subversion wget xerces-c xerces-c-devel libspatialite libspatialite-devel cmake boost-devel bzip2-devel lua-devel nano
	
### 2 - Upgrade Pip: ###

	sudo -H pip install --upgrade pip

### 3 - Compile and install GDAL from source: ###

	user="$(whoami)"
	mkdir /home/$user/gdal_compile
	
	# Download GDAL
	wget http://download.osgeo.org/gdal/2.3.1/gdal-2.3.1.tar.gz -P /home/$user/gdal_compile/
	
	# Download libkml
	wget http://s3.amazonaws.com/etc-data.koordinates.com/gdal-travisci/install-libkml-r864-64bit.tar.gz -P /home/$user/gdal_compile/
	
	# Install libkml
	cd /home/$user/gdal_compile && tar xzf install-libkml-r864-64bit.tar.gz
	sudo cp -r /home/$user/gdal_compile/install-libkml/include/* /usr/local/include
	sudo cp -r /home/$user/gdal_compile/install-libkml/lib/* /usr/local/lib
	sudo ldconfig
	
	# GDAL compilation
	cd /home/$user/gdal_compile
	tar xvzf gdal-2.3.1.tar.gz
	cd /home/$user/gdal_compile/gdal-2.3.1
	./configure --with-libtiff=yes --with-libgeotiff=yes --with-expat=yes --with-sqlite3=yes --with-spatialite=yes --with-geos=yes
	make
	sudo make install


### 4 - Compile and install GRASS GIS from source: ###

	# Set environment variables
	echo "export LD_LIBRARY_PATH=/usr/local/lib" | sudo tee --append /etc/bashrc
	echo "export GDAL_DATA=/usr/local/share/gdal" | sudo tee --append /etc/bashrc
	source /etc/bashrc
	
	# Download GRASS GIS source
	mkdir /home/$user/grass_compile
	wget https://grass.osgeo.org/grass74/source/grass-7.6.0.tar.gz -P /home/$user/grass_compile/
	
	# Compile GRASS GIS and install it
	cd /home/$user/grass_compile
	tar xvzf grass-7.4.0.tar.gz
	cd /home/$user/grass_compile/grass-7.4.0
	./configure --with-cxx --enable-largefile --with-proj --with-proj-share=/usr/share/proj --with-gdal=/usr/local/bin/gdal-config --with-sqlite --with-python --with-cairo --with-cairo-ldflags=-lfontconfig --with-freetype --with-freetype-includes=/usr/include/freetype2 --with-wxwidgets=/usr/bin/wx-config --with-openmp --with-blas --with-blas-includes=/usr/include/atlas-x86_64-base/ --with-lapack --with-lapack-includes=/usr/include/atlas-x86_64-base/ --with-fftw --with-geos --with-netcdf --without-ffmpeg --without-mysql --without-postgres --without-odbc --without-fftw
	make
	sudo make install


### 5 - Install PostgreSQL and PostGIS: ###

	# Install PostgreSQL
	sudo yum -y install https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm
	sudo yum -y install postgresql96 postgresql96-server postgresql96-contrib postgresql96-devel
	sudo /usr/pgsql-9.6/bin/postgresql96-setup initdb
	
	# Edit /var/lib/pgsql/9.6/data/pg_hba.conf
	# Replace "ident" with "md5"
	
	# Enable PGSQL Service
	sudo systemctl enable postgresql-9.6
	sudo systemctl start postgresql-9.6
	
	# Compile and Install PostGIS
	mkdir /home/$user/postgis_compile
	
	wget https://download.osgeo.org/postgis/source/postgis-2.4.4.tar.gz -P /home/$user/postgis_compile
	
	cd /home/$user/postgis_compile
	tar xvzf postgis-2.4.4.tar.gz
	cd postgis-2.4.4
	./configure --with-raster --with-gdalconfig=/usr/local/bin/gdal-config --with-pgconfig=/usr/pgsql-9.6/bin/pg_config
	make
	sudo make install
	
	# Add /usr/local/lib to PGSQL.conf
	echo "/usr/local/lib" | sudo tee --append /etc/ld.so.conf.d/postgresql-pgdg-libs.conf
	sudo ldconfig
	
	# PostGIS basic configuration
	sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'admin';"
	sudo -u postgres psql -c "CREATE EXTENSION postgis;"
	sudo -u postgres psql -c "CREATE EXTENSION postgis_topology;"
	sudo -u postgres createdb postgis_template
	sudo -u postgres psql -d postgis_template -c "UPDATE pg_database SET datistemplate=true WHERE datname='postgis_template'"
	sudo -u postgres psql -d postgis_template -c "CREATE EXTENSION hstore;"
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/postgis.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/postgis_comments.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/spatial_ref_sys.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/rtpostgis.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/raster_comments.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/topology.sql
	sudo -u postgres psql -d postgis_template -f /usr/pgsql-9.6/share/contrib/postgis-2.4/topology_comments.sql