# Developing this site

This is a Jekyll site using locally maintained AcademicPages/Minimal Mistakes layouts. The public URL is https://sbrotee63.github.io. Keep the trailing slash off `url` in `_config.yml` and use `baseurl` only for deployment below a subpath.

## Toolchain and dependencies

- Ruby 3.3.12 and Bundler 2.5.22 (Ruby version recorded in `.ruby-version`).
- Node.js 24.19.0 and npm (`.node-version`).
- `github-pages` 232, matching the published GitHub Pages dependency set at the time of these fixes.
- Commit both `Gemfile.lock` and `package-lock.json`. Do not remove them to solve installation failures.

On Windows, install Ruby+Devkit from [RubyInstaller](https://rubyinstaller.org/downloads/) and complete its MSYS2 setup. Open a new terminal and check `ruby --version` and `bundle --version`. On other platforms use your Ruby version manager; no Windows tools are required there.

From the repository root:

```powershell
bundle install
npm ci
npm run build:js
bundle exec jekyll build --safe
bundle exec ruby scripts/check_site.rb
bundle exec jekyll serve --host 127.0.0.1
```

The preview is at `http://127.0.0.1:4000`. Restart Jekyll after changing `_config.yml`. For a preview with automatic JavaScript rebuilding, run `npm run watch:js` in a second terminal.

Jekyll compiles `assets/css/main.scss`. npm only bundles JavaScript. When changing `assets/js/_main.js` or `assets/js/plugins/`, run `npm run build:js` and include the resulting `assets/js/main.min.js` in the change. Dependency and build directories are ignored by Git and excluded from the public site.

## Content and retained examples

- `_pages/about.md`: biography; `_config.yml`: author profile and site metadata.
- `_data/navigation.yml`: header links.
- `_publications/`: publication records. Supported categories are `books`, `manuscripts` (Journal Articles), and `conferences`; unmatched records still appear under Other Publications.
- `files/CV_Shamyo_Brotee.pdf`: the authoritative CV. `/cv/` and `/resume` redirect to this same PDF. Its editable authoring source is not included; keep that source alongside your own CV workflow and replace this PDF when exporting updates.
- The original photo remains `images/dp.jpg`; the sidebar uses orientation-corrected, compressed `dp-240.jpg` and `dp-480.jpg` derivatives. Preserve the original when updating these.
- Sample posts, talks, teaching entries, portfolio items, and helper pages have `published: false`. The former sample HTML CV is retained in `_drafts/template-cv.md`. Template PDFs and helper scripts are excluded from deployment. To reuse a sample, replace its content and metadata, give it a unique permalink, then remove `published: false`.
- The publication abstract lives once in `excerpt` and is reused by its detail page. `paperurl`, `slidesurl`, and `citation` are independent optional fields.
- MathJax is opt-in with `mathjax: true` in page front matter. A page can opt out of a site-wide setting with `mathjax: false`.
- Generator helpers are optional local tools. Their sample inputs are not the live content source. Read `markdown_generator/readme.md` before running them.

## Verification and publication

Check the homepage, publication listing and detail, CV redirects, and sitemap after shared template edits. Test keyboard navigation and the header/Follow menus at 320, 375, 768, 925, 1024, and 1280 pixels, including resizing with menus open. Check that sample content stays absent and internal resources load successfully.

`scripts/check_site.rb` checks the production `_site` output without external requests: local links/assets/fragments, metadata, downloads, CV redirects, sitemap, and sample exclusions. The optional generators have their own tests: `python -m unittest discover -s markdown_generator -p test_generators.py` (install PyYAML and pybtex for the full suite).

A local build does not deploy. Deployment is controlled by the repository's GitHub Pages settings; there is no checked-in deployment workflow. Confirm the configured source branch/folder in GitHub before changing that setup. Keep the existing publication route and PDF filenames stable so existing links continue working.
