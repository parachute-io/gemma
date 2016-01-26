from urllib import request
import json, re, sublime, sublime_plugin, threading

class GemmaReplaceLineCommand(sublime_plugin.TextCommand):
  def run(self, edit, text):
    selection = self.view.sel()[0]
    line = self.view.line(selection)
    self.view.replace(edit, line, text)

class GemmaCommand(sublime_plugin.TextCommand):
  items = []

  def search_rubygems(self, query):
    status = "Searching RubyGems for '%s'..." % (query)
    self.view.set_status('gemma', status)

    url = "https://rubygems.org/api/v1/search.json?query=%s" % (query)
    req = request.urlopen(url)
    self.view.erase_status('gemma')

    encoding = req.headers.get_content_charset()
    obj = json.loads(req.read().decode(encoding))
    self.handle_rubygems_result(query, obj)


  def handle_rubygems_result(self, query, matches):
    if len(matches) is 0:
      message = "Rubygems had no matches for '%s'" % (query)
      sublime.error_message(message)
      return

    self.items.clear()
    for match in matches:
      self.items.append([match['name'], match['version']])

    window = sublime.active_window()
    window.show_quick_panel(self.items, self.gem_selected)


  def gem_selected(self, selected_index):
    if selected_index < 0:
      return

    item = self.items[selected_index]
    text = "gem '%s', '~> %s'" % (item[0], item[1])
    self.view.run_command('gemma_replace_line', { 'text': text })


  def run(self, edit):
    selection = self.view.sel()[0]
    line = self.view.line(selection)

    if selection.empty() is False:
      gem_name = self.view.substr(selection)
    elif line.empty() is False:
      gem_name = self.view.substr(line).strip()
    else:
      sublime.error_message("Place the cursor on a new line, type a gem name and run the command again.")
      return

    pattern = re.compile('^gem [\'"]([\d\w_-]+)[\'"].*')
    match = pattern.match(gem_name)
    if match is not None:
      gem_name = match.group(1)
    else:
      gem_name = re.sub('[^\d\w_-]', '', gem_name)

    thread = threading.Thread(target=self.search_rubygems, args=(gem_name,))
    thread.start()
