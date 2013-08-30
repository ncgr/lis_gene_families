django
======
This is a proof of concept project that was developed using [django](https://www.djangoproject.com/), a web framework module for Python. The project specifically demonstrates the utility of representing phylogenetic trees in a [Chado](http://www.gmod.org/wiki/Chado) database by providing the user with a rich set of data associated with each node in a tree as well as dynamicly reconstructing the multiple sequence alignment data used to generate the trees.

The components used are:
* [django](http://www.djangoproject.com/)
* [Chado models](https://gist.github.com/danielecook/4494488)
* [D3](http://d3js.org/)
* [jsPhyloSVG](http://www.jsphylosvg.com/)
* [bootswatch](http://bootswatch.com/)

### Running

This project was developed with [Django v1.5.2](https://www.djangoproject.com/download/1.5.2/tarball/), which can be installed following the [installation tutorial](https://www.djangoproject.com/download/).

Once Django is installed you'll want to make sure the tables required by the project have been added to the database. Do this by navigating to the project's root directory and executing:

```
python manage.py syncdb
```
You will be asked if you want to create an admin account for the project. Say yes and enter your credentials.

The project can now be run by navigating to it's root directory and executing:

```
python manage.py runserver
```
This will start a development server that can be accessed at:

```
localhost:8000/chado
````

### Structure

It should be understood that Django uses a Model View Controller (MVC) or Model Template View (MTV) architecture.

Files of interest are located as follows:
* chadotest - the project root directory
    * chadotest - holds project level settings
        * settings.py - sets the database, static directories, etc.
    * chado - the chado application directory
        * models.pl - creates ORM objects
        * views.py - gathers the information for the templates
        * urls.py - defines urls and what template and view are used for each
    * static - contains all the static files that may be served
        * css
        * javascript
    * templates - where all the templates live
        * chado
            * base.html - the template extended by all other templates in the application
            * index.html - the template used for the index page of the application
            * cvterm
            * feature
            * msa
            * organism
            * phylo

### Admin

Django's automatic admin interface has been enabled in this project, but no further work has been done on it. The interface can be accessed at:

```
localhost:8000/admin
```
A good explanation of how to configure the Django admin pages, and of Django in general, is the [Writing your first Django app tutorial](https://docs.djangoproject.com/en/dev/intro/tutorial01/).
