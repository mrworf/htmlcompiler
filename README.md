# htmlcompiler
Takes your HTML file with all dependencies (CSS, JS, images, etc) and produces ONE html file with everything embedded.

Yes, unlike any other tool, this will take all the content needed to display a webpage and inline it.

It will inline the following content:
- Javascript (script tag)
- CSS (link tag)
- Images (img tag and css url())

Known limitations/issues:
- Deals poorly with inline javascript which generates javascript (aka, ad scripts)
- Duplicates images if the same image is used more than once
- File size will be an issue if too much content

Mainly meant for when you want to include a HTML page with graphics and styling but don't feel like having a ton of files to support it. Can be used to convert web pages from the net into a single HTML file (as long as you don't need navigation) but your milage will vary.
