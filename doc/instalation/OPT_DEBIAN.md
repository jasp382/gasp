Optional Software installation on Ubuntu 18.04
====================

## Install MySQL: ##

Install MySQL:

```
sudo apt update
sudo apt install mysql-server
```

Setup MySQL:

```
sudo mysql_secure_installation
```

Create User:

```
sudo mysql -u root -p
CREATE USER 'jasp'@'localhost' IDENTIFIED BY 'jasppP@1';
GRANT ALL PRIVILEGES ON *.* TO 'jasp'@'localhost';
```