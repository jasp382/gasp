GeoData Algorithms for Spatial Problems (GASP)
====================

The GeoData Algorithms for Spatial Problems (GASP) is a free and open source library for geospatial data science.
It consistes of a set of Python Methods to support the automatization of spatial analysis activities based on Geographic Information Systems Software inside any application. These Python Methods could be included in any high-level application for spatial analysis.

GASP Components
====================

### Spatial Analysis algorithms or procedures ###

##### Methods and Algorithms for Land Use/ Land Cover mapping #####

- **OSM2LULC** - implementation in Python of an algorithm for the conversion of OpenStreetMap data into Land Use/Land Cover (LULC) maps. [Know more about OSM2LULC!](/gasp/alg/osm2lulc/)

### Implementation of GIS Software tools ###

- **TODO**

### Data interoperability and data extraction tools ###

- **TODO**

### Tools for Web Frameworks ###

- **TODO**

Installation
====================

### Install dependencies: ###

- [Ubuntu/Debian;](/doc/DOC_DEBIAN.md)
- [Lubuntu;](/doc/DOC_LUBUNTU.md)
- [CentOS7;](/doc/DOC_CENTOS.md)
- MS Windows (TODO).

### Install GASP: ###

1 - Install GIT:

	sudo apt install git

2 - Clone GASP repository from github.com:

	user="$(whoami)"
	mkdir /home/$user/xpto
	cd /home/$user/xpto
	git clone https://github.com/jasp382/gasp3.git

3 - Set PGPASSWORD as environment variable:

	echo "export PGPASSWORD=yourpostgresqlpassword" | sudo tee --append /home/$user/.bashrc
	source /home/$user/.bashrc

4 - Edit /../../gasp/gasp/osm2lulc/con-postgresql.json file according your PostgreSQL configuration;

5 - Replace default osmconf.ini file in your GDAL-DATA configuration folder:

	# For Ubuntu and CentOS
	sudo rm /usr/share/gdal/osmconf.ini
	sudo cp /home/$user/xpto/gasp3/conf/osmconf-gdal.ini /usr/share/gdal/osmconf.ini

	# For CentOS
	sudo rm /usr/local/share/gdal/osmconf.ini
	sudo cp /home/$user/xpto/gasp3/conf/osmconf-gdal.ini /usr/local/share/gdal/osmconf.ini
	
	# For Lubuntu
	sudo rm /usr/share/gdal/2.2/osmconf.ini
	sudo cp /home/$user/xpto/gasp3/conf/osmconf-gdal.ini /usr/share/gdal/2.2/osmconf.ini

6 - Create Python Virtual Environment:

	sudo -H pip install virtualenv
	cd /home/$user/xpto
	virtualenv gasp_env --system-site-packages

7 - Install gasp in the created virtual environment:

	source gasp_env/bin/activate
	cd /home/$user/xpto/gasp
	pip install -r requirements.txt
	python setup.py install

Use GASP without installation
====================

It is possible to use GASP Python package without any configuration. For that, just download the virtual machine vm_gasp using the following URL: https://vgi.uc.pt/vgi/vm/vm_gasp/

The only requirement is to have 7Zip and VirtualBox 5.x installed. The first to decompress the vm_gasp.7z and the second to run the virtual machine (vm_gasp.vbox).

The access to the virtual machine is performed with the following credentials:

<b>User: </b>gisuser
<br>
<b>Password: </b>gisuser

To test GASP tools, just activate the virtual python environment with the name gasp_env, as shown in the following example:

	cd /home/gisuser/xpto/gasp
	source gasp_env/bin/activate

Also to test GASP, anyone can use the data available in the /home/gisuser/sample_data folder.

Documentation
====================
TODO

Development
====================
TODO

Bug reports
====================
<b>If a bug is found or if there is any problem during GASP setup, please send an email to the administrator of this repository (jpatriarca@mat.uc.pt).</b>

License information
====================

See the file \"LICENSE\" for information about the terms & conditions and a DISCLAIMER OF ALL WARRANTIES.