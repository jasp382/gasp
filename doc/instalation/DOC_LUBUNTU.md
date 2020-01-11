Install GASP Dependencies in Lubuntu 16.04
====================

### 1 - Install Python and Pip: ###

	sudo apt update
	sudo apt install python python-pip
	sudo -H pip install --upgrade pip

### 2 - Install GDAL and GRASS GIS: ###

	sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
	sudo apt update && sudo apt upgrade
	sudo apt install grass grass-dev
	sudo apt install python-gdal
	
	# Set GDALDATA environment variable
	user="$(whoami)"
	echo "export GDAL_DATA=/usr/share/gdal/2.2" | sudo tee --append /home/$user/.bashrc
	source /home/$user/.bashrc

### 3 - Install PostgreSQL and PostGIS: ###

	# Install PostgreSQL
	sudo apt install build-essential
	echo 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main' | sudo tee --append /etc/apt/sources.list
	wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
	sudo apt update && sudo apt upgrade
	sudo apt install postgresql-11 postgresql-server-dev-11 libxml2-dev xsltproc docbook-xsl docbook-mathml
	
	# Install PostGIS
	sudo apt install -y postgis postgresql-11-postgis-2.5
	
	# PostGIS basic configuration
	sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'admin';"
	sudo -u postgres psql -c "CREATE EXTENSION postgis;"
	sudo -u postgres psql -c "CREATE EXTENSION postgis_topology;"
	sudo -u postgres createdb postgis_template
	sudo -u postgres psql -d postgis_template -c "UPDATE pg_database SET datistemplate=true WHERE datname='postgis_template'"
	sudo -u postgres psql -d postgis_template -c "CREATE EXTENSION hstore;"
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/postgis.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/postgis_comments.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/spatial_ref_sys.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/rtpostgis.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/raster_comments.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/topology.sql
	sudo -u postgres psql -d postgis_template -f /usr/share/postgresql/11/contrib/postgis-2.5/topology_comments.sql
	