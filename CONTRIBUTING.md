# Contributing to gfspy
Thank you for taking the time to contribute and for checking out these guidelines.
## Table of content

[Have a problem?](#have-a-problem)

[Helping out](#helping-out)
- [What you need to know](#what-do-i-need-to-know-before-i-start)
- [The contribution process](#the-contribution-process)
- [Comments and docstrings](#comments-and-docstrings)
- [Autoformatting with black](#autoformatting-with-black)
- [Building sphinx documentation](#building-sphinx-documentation)

## Have a problem?
If you have a problem you have thre courses of action:
1. Ask for help - if you aren't sure how something works please check out the documentation (work in progress) and if you don't find an answer there start a [discussion](https://github.com/jagoosw/gfspy/discussions)
2. Open an issue - if you think there is a problem with the software then please open an [issue](https://github.com/jagoosw/gfspy/issues) (if you have a question please use the discussion instead of issues)
3. Fix it - if you know how to fix your problem then please follow the contribution guidlines below

## Helping out
We are always looking for help with this project, the main need is more coding but if you can't do that please get in touch as we have lots of holes in the (documentation)[] and could do with administrative help too. 
### What do I need to know before I start
Although this project didn't have firm conventions from the start we are trying to formalise them to make the code more readable and easier to modify. Some pointers for now are:
- Functionality that requires more than one class method should be in their own file
- Try to stick to the [black](https://github.com/psf/black#the-black-code-style) coding style, instructions below for automation
- We use [Sphinx](https://www.sphinx-doc.org/en/master/) for API documentation so comments must be in a very specific format
- **When you modify code this usually has a knock on effect. This means when you make a change you should try to make it backwards compatiable or go through the other files and modify them to accomodate your changes. This usually includes modifcation to `example.py`, `statistical.py` (this could be complicated so please contact us to check how we want the changes implimented in it), `stats_example.py`, `example.ipynb`, `stats_example.ipynb` and `main.py` if you have made changes in another file. If your code includes a new functionality you should change the examples to be able to demonstrait that.**
- We have a [code of conduct](https://github.com/cuspaceflight/gfspy/blob/main/CODE_OF_CONDUCT.md). TLDR - be nice to other people.

### The contribution process

1. If you are a first time contributor
- Go to the project [home page](https://github.com/jagoosw/gfspy) and click "fork" in the top right of the page
- Clone the repository to your computer either with the [desktop app](https://desktop.github.com/) or by

```git clone https://github.com/your-username/gfspy.git```
- Add the upstream by going into the directory (`cd gfspy`) and then 
- 
```git remote add upstream https://github.com/jagoosw/gfspy.git```
2. Develop your contribution:
- Update to get the latest changes by pulling it in with the website or

```git checkout main```

```git pull upstream main```
- Create a branch for your contribution with the desktop app or

```git checkout -b branch-name```
- Create and add your contributions locally (`git add` and `git commit`)
3. Test your code
- Before you push your code please please please run thorough tests on it so the reviewers don't have to
- This should include (at the minimum) running an example file and the stats example (because this sort of tests for edge cases randomly) and if you have made a change that changes the physics of the simulation a thorough analysis of the difference in results to determine if it is implimented correctly
- If you have added something that can be tested on its own please do a thorough test as a unit (if you need inspiration for a testing stratagy please make a discussion). For example if you have added a new recovery method that has dependance on altitude and velocity make a file where you import the class and request the forces from it over a range of velocities and altitudes and see if it is as you would expect.
- Keep a record of these teste (e.g. screenshots of outputs showing problems or expected behaviours)
5. Submit your contribution
- Push your changes to your fork on github 

``git push origin branch-name``

- Go to the your Github page (`https://github.com/your-username/gfspy`) and onto the branch where there will be a green button asking if you want to make a pull request, alternativly click pull request in the top bar
- Create a pull request from your branch to the main branch of `https://github.com/jagoosw/gfspy` with a clear title, explanation of what your code does and any maths/physics that are not obvious that you have implimented and details of the tests you ran and their results (example plots etc. would be nice especially if they are different before and after your change)

6. Review
- There is now an automatic test case that runs a shortened version of the example file. This is to check that your changes do not break the core functionality and so if you change something core (e.g. how aeros work) then the test case will fail. Please check the reason that your test failed and if it is because one of the tests actually fails (rather than the test not being able to run) then contact me and we will look at if the test needs changing.
- We will have a look at the pull request as soon as we can and go through it, possibly testing the code ourselves
- We are likely to suggest changes to style or funcitonality (please don't be offended, we have spent so much of our time working on it we don't want anything to break or be wrong)
- Once this is done we will pull it into the main branch 


#### Comments and docstrings
Please try to document your code so you and everyone else knows whats going on. This should at a minimum include adding or updating a [Google style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) docstring for each function/method and class. A few points to note are:
- Docstrings must be surrounded by `"""` not `'''` 
- Other comments should not use `"""` as they will show up in random places in the documentation
- Docstrings are whitespace sensiative - you must leave a line space between sections (follow the examples closely)
- Titles (like `Note`) must have a line of `-` under them that is as long as the line (e.g. `Note↵----`)
Other comments to help with your code (e.g. descriptions of what sections do) should ise `#` sytle comments - please use often (we haven't been good at this)

#### Autoformatting with black
To make the code cleaner and more consistent we are starting to use black autoformatting. To use `pip install black` and then `black director-name`. For more information see the link above. At some point we will transition to have git force you to use this before in which case you will need to install [pre-commit](https://pre-commit.com/).

#### Building sphinx documentation
When you make changes these are not automatically added to the documentation (especially since the docs work out of a different repo). You will need to [install sphinx](https://www.sphinx-doc.org/en/master/usage/installation.html) then enter `docs/` and then `make html` to update the docs. 
