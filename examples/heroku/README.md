# geemap-heroku

Python scripts for deploying Earth Engine Apps to heroku, try it out: <https://geemap-demo.herokuapp.com/>

## How to deploy your own Earth Engine Apps?

- [Sign up](https://signup.heroku.com/) for a free heroku account.
- Follow the [instructions](https://devcenter.heroku.com/articles/getting-started-with-python#set-up) to install [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and Heroku Command Line Interface (CLI).
- Authenticate heroku using the `heroku login` command.
- Clone this repository: <https://github.com/giswqs/geemap-heroku>
- Create your own Earth Engine notebook and put it under the `notebooks` directory.
- Add Python dependencies in the `requirements.txt` file if needed.
- Edit the `Procfile` file by replacing `notebooks/geemap.ipynb` with the path to your own notebook.
- Commit changes to the repository by using `git add . && git commit -am "message"`.
- Create a heroku app: `heroku create`
- Run the `config_vars.py` script to extract Earth Engine token from your computer and set it as an environment variable on heroku: `python config_vars.py`
- Deploy your code to heroku: `git push heroku master`
- Open your heroku app: `heroku open`

## Optional steps

- To specify a name for your app, use `heroku apps:create example`
- To preview your app locally, use `heroku local web`
- To hide code cells from your app, you can edit the `Procfile` file and set `--strip_sources=True`
- To periodically check for idle kernels, you can edit the `Procfile` file and set `--MappingKernelManager.cull_interval=60 --MappingKernelManager.cull_idle_timeout=120`
- To view information about your running app, use `heroku logs --tail`
- To set an environment variable on heroku, use `heroku config:set NAME=VALUE`
- To view environment variables for your app, use `heroku config`

## Credits

The instructions above on how to deploy a voila application on heroku are adapted from [voila-dashboards/voila-heroku](https://github.com/voila-dashboards/voila-heroku).
