Equilibrium
==============
Work made easy.

Equilibrium is managing *projects deadlines* within a workplace/ﬁrm etc more social. So that workplaces can have a centralized
social way of looking into various ongoing projects and organize them in such a way that results in a more productive environment.

This application was submitted for *Google Cloud Developer Challenge 2013* and was among one of the [finalists](http://www.google.com/events/gcdc2013/finalists.html) for India region.

<p align="center">
  <img src="https://gcdc2013-equilibrium.appspot.com/img/Hinder2.png" style="height: 192px;width:192px;" alt="Equilibrium - GCDC">
</p>

<p align="center">
https://gcdc2013-equilibrium.appspot.com/
</p>


Tech Stack
----------

* Google App Engine
* Google Data Store
* Python
* Flask, Jinja2
* Google Maps API
* Google+ Signin
* Google Custom Search API
* Wikipedia API
* Google Translate toolkit
* SimpleAuth(https://github.com/crhym3/simpleauth)



Development
-----------

* Clone this repo (`git clone git@github.com:yashrajsingh/Equilibrium-GCDC2013.git`)
* Download [Python SDK](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python "Python SDK for Google App Engine") for Google App Engine
* Unzip the downloaded SDK
* Change directory to project directory (`cd ~/path/to/Equilibrium-GCDC2013`)
* Change the application keys:
	- Add your secret keys for social networks in `secrets.py`.
	- Add your Google Maps Key in `templates/projects.html` and `templates/firm.html`.
	- Add your Google Custom Search key and cx in `handlers.py`.
	
* Run the application locally (`~/path/to/sdk/dev_appserver.py .`)
* Visit `http://localhost:8080/` using your browser to see it in action.



Help and Support
--------------

[Homepage](https://gcdc2013-equilibrium.appspot.com/)

[Yash Raj Singh](http://yashrajsingh.net/)