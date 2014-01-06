// Generated by CoffeeScript 1.6.1
(function() {
  var $, do_postable_filter, do_postable_info, do_tags, h, parse_querystring, root,
    __hasProp = {}.hasOwnProperty,
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  $ = jQuery;

  h = teacup;

  parse_querystring = function(qstr) {
    var q, qlist;
    qlist = qstr.split('&');
    qlist = _.difference(qlist, ['query=tagtype:ads/tagtype:tag']);
    qlist = (function() {
      var _i, _len, _results;
      _results = [];
      for (_i = 0, _len = qlist.length; _i < _len; _i++) {
        q = qlist[_i];
        _results.push(q.replace('query=tagname:', ''));
      }
      return _results;
    })();
    if (qlist.length === 1 && qlist[0] === "") {
      qlist = [];
    }
    return qlist;
  };

  do_postable_info = function(sections, config, ptype) {
    return $.get(config.infoURL, function(data) {
      var content;
      if (ptype === 'library') {
        content = views.library_info(data, templates.library_itemsinfo);
      } else if (ptype === 'group') {
        content = views.group_info(data, templates.group_itemsinfo);
      }
      sections.$info.append(content + '<hr/>');
      return sections.$info.show();
    });
  };

  do_tags = function(url, $sel, tqtype) {
    return $.get(url, function(data) {
      var k, v, _ref, _results;
      _ref = data.tags;
      _results = [];
      for (k in _ref) {
        if (!__hasProp.call(_ref, k)) continue;
        v = _ref[k];
        _results.push(format_tags(k, $sel, get_tags(v, tqtype), tqtype));
      }
      return _results;
    });
  };

  do_postable_filter = function(sections, config, tagfunc) {
    var loc, nonqloc, urla;
    tagfunc();
    $.get("" + config.tagsucwtURL + "?tagtype=ads/tagtype:tag", function(data) {
      var e, qtxtlist, suggestions, _i, _len;
      suggestions = data.simpletags;
      qtxtlist = parse_querystring(config.querystring);
      if (qtxtlist.length > 0) {
        sections.$breadcrumb.text('Tags: ');
        for (_i = 0, _len = qtxtlist.length; _i < _len; _i++) {
          e = qtxtlist[_i];
          if (e === "userthere=true") {
            e = "Posted by you";
          }
          sections.$breadcrumb.append("<span class='badge'>" + e + "</span>&nbsp;");
        }
        sections.$breadcrumb.show();
      }
      return $.get(config.itemsPURL, function(data) {
        var biblist, bibstring, i, itemlist, itemsq, thecount, theitems;
        theitems = data.items;
        sections.$count.text("" + theitems.length + " papers. ");
        sections.$count.show();
        thecount = data.count;
        itemlist = (function() {
          var _j, _len1, _results;
          _results = [];
          for (_j = 0, _len1 = theitems.length; _j < _len1; _j++) {
            i = theitems[_j];
            _results.push(i.basic.fqin);
          }
          return _results;
        })();
        biblist = (function() {
          var _j, _len1, _results;
          _results = [];
          for (_j = 0, _len1 = theitems.length; _j < _len1; _j++) {
            i = theitems[_j];
            _results.push(i.basic.name);
          }
          return _results;
        })();
        bibstring = biblist.join("\n");
        sections.$bigquery.val(bibstring);
        sections.$bigqueryform.attr("action", config.bq2url);
        itemsq = itemlist.join("&");
        return syncs.taggings_postings_post_get(itemlist, config.pview, function(data) {
          var cb, eb, ido, k, notes, plinv, postings, ptimes, sorteditems, stags, times, v, _j, _len1, _ref, _ref1;
          _ref = get_taggings(data), stags = _ref[0], notes = _ref[1];
          postings = {};
          times = {};
          _ref1 = data.postings;
          for (k in _ref1) {
            if (!__hasProp.call(_ref1, k)) continue;
            v = _ref1[k];
            if (v[0] > 0) {
              postings[k] = (function() {
                var _j, _len1, _ref2, _results;
                _ref2 = v[1];
                _results = [];
                for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
                  e = _ref2[_j];
                  _results.push([e.posting.postfqin, e.posting.postedby]);
                }
                return _results;
              })();
              ptimes = (function() {
                var _j, _len1, _ref2, _results;
                _ref2 = v[1];
                _results = [];
                for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
                  e = _ref2[_j];
                  if (e.posting.postfqin === config.fqpn) {
                    _results.push(e.posting.whenposted);
                  }
                }
                return _results;
              })();
              if (ptimes.length > 0) {
                times[k] = ptimes[0];
              } else {
                times[k] = 0;
              }
            } else {
              postings[k] = [];
              times[k] = 0;
            }
          }
          sorteditems = _.sortBy(theitems, function(i) {
            return -Date.parse(times[i.basic.fqin]);
          });
          for (_j = 0, _len1 = sorteditems.length; _j < _len1; _j++) {
            i = sorteditems[_j];
            i.whenposted = times[i.basic.fqin];
          }
          ido = {
            stags: stags,
            postings: postings,
            notes: notes,
            $el: sections.$items,
            items: sorteditems,
            noteform: true,
            nameable: false,
            itemtype: 'ads/pub',
            memberable: config.memberable,
            suggestions: suggestions,
            pview: config.pview,
            tagfunc: tagfunc
          };
          plinv = new itemsdo.ItemsFilterView(ido);
          plinv.render();
          eb = function(err) {
            var d, _k, _len2, _results;
            _results = [];
            for (_k = 0, _len2 = theitems.length; _k < _len2; _k++) {
              d = theitems[_k];
              _results.push(format_item(plinv.itemviews[d.basic.fqin].$('.searchresultl'), d));
            }
            return _results;
          };
          cb = function(data) {
            var d, docnames, thedocs, _k, _l, _len2, _len3, _ref2, _ref3, _results;
            thedocs = {};
            _ref2 = data.response.docs;
            for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
              d = _ref2[_k];
              thedocs[d.bibcode] = d;
            }
            docnames = (function() {
              var _l, _len3, _ref3, _results;
              _ref3 = data.response.docs;
              _results = [];
              for (_l = 0, _len3 = _ref3.length; _l < _len3; _l++) {
                d = _ref3[_l];
                _results.push(d.bibcode);
              }
              return _results;
            })();
            _results = [];
            for (_l = 0, _len3 = theitems.length; _l < _len3; _l++) {
              d = theitems[_l];
              if (_ref3 = d.basic.name, __indexOf.call(docnames, _ref3) >= 0) {
                e = thedocs[d.basic.name];
              } else {
                e = {};
              }
              plinv.itemviews[d.basic.fqin].e = e;
              _results.push(format_item(plinv.itemviews[d.basic.fqin].$('.searchresultl'), e));
            }
            return _results;
          };
          return syncs.send_bibcodes(config.bq1url, theitems, cb, eb);
        });
      });
    });
    loc = config.loc;
    nonqloc = loc.href.split('?')[0];
    if (sections.$ua.attr('data') === 'off') {
      if (nonqloc === loc.href) {
        urla = loc + "?userthere=true";
      } else {
        urla = loc + "&userthere=true";
      }
      sections.$ua.attr('href', urla);
      return sections.$ua.attr('data', 'on');
    }
  };

  root.postablefilter = {
    do_postable_info: do_postable_info,
    do_postable_filter: do_postable_filter,
    do_tags: do_tags
  };

}).call(this);
