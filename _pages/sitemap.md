---
layout: archive
title: "Sitemap"
permalink: /sitemap/
author_profile: true
---

{% include base_path %}

A list of all the posts and pages found on the site. For you robots out there is an [XML version]({{ base_path }}/sitemap.xml) available for digesting as well.

<h2>Pages</h2>
{% for post in site.pages %}
  {% unless post.sitemap == false or post.redirect_to or post.published == false %}
    {% if post.title or post.url == '/' %}
      {% include archive-single.html %}
    {% endif %}
  {% endunless %}
{% endfor %}

{% if site.posts.size > 0 %}
<h2>Posts</h2>
{% for post in site.posts %}
  {% unless post.sitemap == false or post.published == false %}
    {% include archive-single.html %}
  {% endunless %}
{% endfor %}
{% endif %}

{% for collection in site.collections %}
  {% unless collection.output == false or collection.label == "posts" %}
    {% assign collection_title_shown = false %}
    {% for post in collection.docs %}
      {% unless post.sitemap == false or post.published == false %}
        {% unless collection_title_shown %}
<h2>{{ collection.label | capitalize }}</h2>
          {% assign collection_title_shown = true %}
        {% endunless %}
        {% include archive-single.html %}
      {% endunless %}
    {% endfor %}
  {% endunless %}
{% endfor %}
