# Game Catalog Web App
This is a web application that has a list of games that sorted by themes. It also uses third-party authentication
and authorization service (Google Account) to login. User in this app will only allow to edit, delete, create their
own theme or their own games.

## Install
1. Install Vagrant and VirtualBox
2. clone the fullstack-nanodegree-vm
2. download all the files in the repo **game_catalog_webapp** 
   ---make sure all the files are located at fullstack-nanodegree-vm/vagrant/catalog folder
3. **vagrant up** at your terminal
   **make sure the path of the terminal is at vagrant file**
4. **vagrant ssh** at your terminal too
5. **cd /vagrant**
6. **cd catalog**
7. **ls** ---make sure you have all the files
8. please install the following python wrapper
```
    sudo pip install igdb_api_python
```

## Instruction for running the program
1. make sure you are at /vagrant/catalog directory
2. run **python database_setup.py**
3. run **python lotsofgames.py**
4. run **python application.py**
5. you can visit [http://localhost:8000](http://localhost:8000) locally

## Attribution
1. Thanks for [IGDB API](https://www.igdb.com/api) to provide free video game database
2. Thanks for [GOOGLE API](https://developers.google.com/)
3. Thanks for [Udacity](https://www.udacity.com/) to provide fullstack-nanodegree-vm
