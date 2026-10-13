#!/usr/bin/env ruby
# Run after a production build: bundle exec ruby scripts/check_site.rb [output-directory]
# Checks local output only; never requests external URLs.
require "date"
require "json"
require "nokogiri"
require "pathname"
require "set"
require "uri"
require "yaml"

class SiteCheck
  def initialize(source, output)
    @source = source
    @output = output
    @config = YAML.safe_load(File.read(File.join(source, "_config.yml")),
                             permitted_classes: [Date, Time], aliases: true)
    @origin = URI.parse(@config.fetch("url"))
    @baseurl = @config.fetch("baseurl", "").to_s.sub(%r{/$}, "")
    @site_url = "#{@origin}#{@baseurl}/"
    @errors = Set.new
    @documents = {}
    @references = 0
  end

  def assert(condition, message)
    @errors << message unless condition
  end

  def relative(file)
    Pathname.new(file).relative_path_from(Pathname.new(@output)).to_s.tr("\\", "/")
  end

  def document(file)
    @documents[file] ||= Nokogiri::HTML(File.read(file))
  end

  def page_url(file)
    path = relative(file).sub(%r{(^|/)index\.html$}, '\\1')
    "#{@site_url}#{path}"
  end

  def target_file(path)
    decoded = URI::DEFAULT_PARSER.unescape(path)
    return nil unless @baseurl.empty? || decoded == @baseurl || decoded.start_with?("#{@baseurl}/")

    local = decoded.delete_prefix(@baseurl).sub(%r{^/}, "")
    expanded = File.expand_path(local, @output)
    return nil unless expanded == @output || expanded.start_with?("#{@output}/")

    [expanded, File.join(expanded, "index.html"), "#{expanded}.html"].find { |candidate| File.file?(candidate) }
  end

  def check_reference(raw, source_file, kind)
    value = raw.to_s.strip
    return if value == "#" || value.empty?
    uri = URI.join(page_url(source_file), URI::DEFAULT_PARSER.escape(value, /[^\x00-\x7F]/))
    return unless %w[http https].include?(uri.scheme) && uri.host == @origin.host

    @references += 1
    assert(!uri.path.include?("//"), "#{relative(source_file)}: doubled slash in #{kind} #{value}")
    target = target_file(uri.path)
    unless target
      @errors << "#{relative(source_file)}: missing #{kind} target #{value}"
      return
    end
    fragment = URI::DEFAULT_PARSER.unescape(uri.fragment.to_s.split(":~:", 2).first.to_s)
    return if fragment.empty?

    if File.extname(target).downcase == ".html"
      found = document(target).xpath("//*[@id] | //a[@name]").any? do |node|
        node["id"] == fragment || node["name"] == fragment
      end
      assert(found, "#{relative(source_file)}: missing fragment #{value}")
    elsif File.extname(target).downcase == ".svg"
      found = Nokogiri::XML(File.read(target)).xpath("//*[@id]").any? { |node| node["id"] == fragment }
      assert(found, "#{relative(source_file)}: missing SVG fragment #{value}")
    end
  rescue URI::InvalidURIError => error
    @errors << "#{relative(source_file)}: invalid #{kind} URL #{value.inspect}: #{error.message}"
  end

  def check_css(text, file)
    text.scan(/url\(\s*(?:(["'])(.*?)\1|([^)]*))\s*\)/m).each do |_, quoted, unquoted|
      check_reference(quoted || unquoted, file, "CSS")
    end
    text.scan(/@import\s+["']([^"']+)["']/).flatten.each do |url|
      check_reference(url, file, "CSS import")
    end
  end

  def check_html(file)
    doc = document(file)
    doc.css("[href], [src], [poster], [data]").each do |node|
      %w[href src poster].each do |attribute|
        check_reference(node[attribute], file, attribute) if node.key?(attribute)
      end
      check_reference(node["data"], file, "object data") if node.name == "object"
    end
    doc.css("[srcset]").each do |node|
      next if node["srcset"].start_with?("data:")
      node["srcset"].split(",").each { |entry| check_reference(entry.strip.split.first, file, "srcset") }
    end
    doc.css("[style]").each { |node| check_css(node["style"], file) }
    doc.css("style").each { |node| check_css(node.text, file) }
    doc.css('meta[name="msapplication-TileImage"], meta[name="msapplication-config"], meta[property="og:image"], meta[name="twitter:image"]').each do |node|
      check_reference(node["content"], file, "metadata asset")
    end
    doc.css('script[type="application/ld+json"]').each do |node|
      data = JSON.parse(node.text)
      [data].flatten.each do |profile|
        next unless profile.is_a?(Hash)
        assert(!profile.key?("sameAs") || profile["sameAs"].is_a?(Array), "#{relative(file)}: sameAs must be an array when present")
        check_reference(profile["image"], file, "JSON-LD image") if profile["image"].is_a?(String)
      end
    rescue JSON::ParserError => error
      @errors << "#{relative(file)}: invalid JSON-LD: #{error.message}"
    end
  end

  def check_home
    file = File.join(@output, "index.html")
    return assert(false, "Homepage index.html is missing") unless File.file?(file)
    home = document(file)
    assert(home.css("h1").size == 1 && !home.at_css("h1").text.strip.empty?, "Homepage must have one meaningful H1")
    description = home.at_css('meta[name="description"]')&.[]("content")
    assert(description && !description.strip.empty? && description != "This page will contain the news about my life", "Homepage needs a personal meta description")
    assert(home.at_css('meta[property="og:description"]')&.[]("content") == description, "Homepage OG description differs from its meta description")
    assert(home.at_css('link[rel="canonical"]')&.[]("href") == @site_url, "Homepage canonical URL must match configured production URL")
    assert(home.at_css('meta[property="og:url"]')&.[]("content") == @site_url, "Homepage OG URL must match its canonical")
    avatar = home.at_css(".author__avatar img")
    assert(avatar && !avatar["alt"].to_s.empty? && avatar["width"].to_i.positive? && avatar["height"].to_i.positive?, "Homepage avatar needs alt text and intrinsic dimensions")
    assert(avatar && avatar["srcset"].to_s.split(",").length >= 2, "Homepage avatar should offer responsive image sizes")
    assert(home.css("script[src]").none? { |script| script["src"].match?(/mathjax|polyfill/i) }, "Homepage must not download unused MathJax or polyfills")
    profiles = home.css('script[type="application/ld+json"]').filter_map { |node| JSON.parse(node.text) rescue nil }
    assert(profiles.any? { |profile| profile["@type"] == "Person" && profile["name"] == @config.dig("author", "name") }, "Homepage needs Person metadata for the site author")
    assert(home.at_css('a[href="#main"]') && home.at_css('#main[tabindex="-1"]'), "Homepage skip link needs a focusable main target")
  end

  def check_publications
    files = Dir.glob(File.join(@source, "_publications", "*.{md,markdown,html}"))
    published = files.filter_map do |file|
      data = front_matter(file)
      data if data && data["published"] != false
    end
    assert(!published.empty?, "No published research remains")
    published.each do |data|
      target = target_file("#{@baseurl}#{data.fetch("permalink")}")
      unless target
        @errors << "Missing publication page #{data['permalink']}"
        next
      end
      next unless data["paperurl"]
      links = document(target).css("a[href]")
      assert(links.any? { |link| link["href"] == data["paperurl"] && link.text.match?(/Download Paper/i) },
             "Publication #{data['permalink']} must link to its paper")
      assert(!document(target).at_css("main, #main").text.include?("{{ page.excerpt }}"), "Publication contains unrendered abstract Liquid")
    end
  end

  def front_matter(file)
    text = File.read(file)
    yaml = text[/\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n/m, 1]
    YAML.safe_load(yaml, permitted_classes: [Date, Time], aliases: true) if yaml
  end

  def check_redirects
    { "/cv/" => "/files/CV_Shamyo_Brotee.pdf", "/resume" => "/cv/",
      "/about/" => "/", "/about.html" => "/",
      "/wordpress/blog-posts/" => "/year-archive/" }.each do |route, destination|
      file = target_file("#{@baseurl}#{route}")
      unless file
        @errors << "Missing redirect route #{route}"
        next
      end
      doc = document(file)
      expected = "#{@origin}#{@baseurl}#{destination}"
      assert(doc.at_css('link[rel="canonical"]')&.[]("href") == expected, "#{route} should redirect to #{destination}")
      refresh = doc.css("meta").find { |node| node["http-equiv"].to_s.downcase == "refresh" }
      refresh_target = refresh&.[]("content").to_s[/\A\s*0\s*;\s*url\s*=\s*(.+)\z/i, 1]
      assert(refresh_target && URI.join("#{@origin}/", refresh_target).to_s == expected,
             "#{route} needs an automatic redirect to #{destination}")
      assert(refresh_target == "#{@baseurl}#{destination}", "#{route} must stay on the current preview origin")
    end
  end

  def check_archives
    %w[sitemap page-archive].each do |route|
      file = target_file("#{@baseurl}/#{route}/")
      next unless file
      links = document(file).css(".archive__item-title a")
      assert(!links.empty?, "#{route} must list meaningful pages")
      links.each { |link| assert(!link.text.strip.empty?, "#{route} contains an empty archive link") }
      assert(links.none? { |link| link["href"].match?(%r{/(404\.html|feed\.xml|sitemap\.xml|cv/|resume(?:\.html)?)$}) }, "#{route} lists utility/redirect pages")
    end
    sitemap_file = File.join(@output, "sitemap.xml")
    assert(File.file?(sitemap_file), "sitemap.xml is missing")
    if File.file?(sitemap_file)
      Nokogiri::XML(File.read(sitemap_file)).remove_namespaces!.css("loc").each do |node|
        check_reference(node.text, sitemap_file, "XML sitemap")
      end
    end
  end

  def check_exclusions
    Dir.glob(File.join(@source, "{_pages,_posts,_portfolio,_talks,_teaching}", "*.{md,markdown,html}")).each do |file|
      data = front_matter(file)
      next unless data && data["published"] == false
      route = data["permalink"]
      route ||= "/#{data['collection']}/#{File.basename(file, '.*')}/" if data["collection"]
      assert(!target_file("#{@baseurl}#{route}"), "Unpublished sample still has output: #{route}") if route
    end
    %w[talkmap markdown_generator scripts CONTRIBUTING.md DEVELOPMENT.md package-lock.json Gemfile.lock].each do |path|
      assert(!File.exist?(File.join(@output, path)), "Development/sample artifact is published: #{path}")
    end
    Dir.glob(File.join(@output, "files", "{paper,slides}[123].pdf")).each do |file|
      @errors << "Sample download is published: #{relative(file)}"
    end
    @documents.each do |file, doc|
      assert(!doc.at_css("body")&.text.to_s.match?(/GitHub University|Ph\.D in Version Control Theory|Blog Post number \d|Portfolio item number \d|Future Blog Post/i),
             "#{relative(file)} contains template sample content")
    end
  end

  def run
    abort "Build output not found: #{@output}. Run bundle exec jekyll build first." unless Dir.exist?(@output)
    html = Dir.glob(File.join(@output, "**", "*.html"))
    html.each { |file| check_html(file) }
    Dir.glob(File.join(@output, "**", "*.css")).each { |file| check_css(File.read(file), file) }
    manifest_file = File.join(@output, "images", "manifest.json")
    if File.file?(manifest_file)
      JSON.parse(File.read(manifest_file)).fetch("icons", []).each do |icon|
        check_reference(icon["src"], manifest_file, "manifest icon")
      end
    end
    check_home
    check_publications
    check_redirects
    check_archives
    check_exclusions
    if @errors.empty?
      puts "PASS: #{html.size} HTML pages, #{@references} internal references, CSS assets, metadata, publication downloads, redirects, archives, and sample exclusions."
      true
    else
      warn "FAIL: #{@errors.size} issue(s):"
      @errors.sort.each { |error| warn "  - #{error}" }
      false
    end
  end
end

source = File.expand_path("..", __dir__)
output = File.expand_path(ARGV[0] || "_site", source)
exit(SiteCheck.new(source, output).run ? 0 : 1)

