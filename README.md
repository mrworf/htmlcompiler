# htmlcompiler
Takes your HTML file with all dependencies (CSS, JS, images, etc) and produces ONE html file with everything embedded.

Yes, unlike any other tool, this will take all the content needed to display a webpage and inline it. There are of course some limitations, it will not deal with dynamically generated URLs.

It will inline the following content:
- Javascript
- CSS
- Images (<img/> and css)
