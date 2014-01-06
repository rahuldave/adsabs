// Generated by CoffeeScript 1.6.1
(function() {
  var $, do_postform, h, root,
    __hasProp = {}.hasOwnProperty,
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  $ = jQuery;

  h = teacup;

  do_postform = function(sections, config) {
    var $itemssec, itemsInfoURL, itemsTPURL, itemstring, itemtype, loc, memberable, nam, tagsucwtURL;
    itemstring = config.itemstring, itemsInfoURL = config.itemsInfoURL, itemsTPURL = config.itemsTPURL, tagsucwtURL = config.tagsucwtURL, memberable = config.memberable, itemtype = config.itemtype, nam = config.nam, loc = config.loc;
    $itemssec = sections.$itemssec;
    return $.get("" + tagsucwtURL + "?tagtype=ads/tagtype:tag", function(data) {
      var suggestions;
      suggestions = data.simpletags;
      return syncs.post_for_itemsinfo(itemsInfoURL, itemstring, function(data) {
        var i, itemlist, itemsq, thecount, theitems;
        theitems = data.items;
        thecount = data.count;
        itemlist = (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = theitems.length; _i < _len; _i++) {
            i = theitems[_i];
            _results.push(i.basic.fqin);
          }
          return _results;
        })();
        itemsq = itemlist.join("&");
        return syncs.taggings_postings_post_get(itemlist, 'none', function(data) {
          var cb, e, eb, ido, k, notes, plinv, postings, stags, v, _ref, _ref1;
          _ref = get_taggings(data), stags = _ref[0], notes = _ref[1];
          postings = {};
          _ref1 = data.postings;
          for (k in _ref1) {
            if (!__hasProp.call(_ref1, k)) continue;
            v = _ref1[k];
            if (v[0] > 0) {
              postings[k] = (function() {
                var _i, _len, _ref2, _results;
                _ref2 = v[1];
                _results = [];
                for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
                  e = _ref2[_i];
                  _results.push(e.posting.postfqin);
                }
                return _results;
              })();
            } else {
              postings[k] = [];
            }
          }
          ido = {
            stags: stags,
            postings: postings,
            notes: notes,
            $el: $itemssec,
            items: theitems,
            noteform: false,
            nameable: nam,
            itemtype: itemtype,
            memberable: memberable,
            loc: loc,
            suggestions: suggestions,
            pview: 'none'
          };
          if (thecount === 1) {
            ido.noteform = true;
          }
          plinv = new itemsdo.ItemsView(ido);
          plinv.render();
          eb = function(err) {
            var d, _i, _len, _results;
            _results = [];
            for (_i = 0, _len = theitems.length; _i < _len; _i++) {
              d = theitems[_i];
              _results.push(format_item(plinv.itemviews[d.basic.fqin].$('.searchresultl'), d));
            }
            return _results;
          };
          cb = function(data) {
            var d, docnames, thedocs, _i, _j, _len, _len1, _ref2, _ref3, _results;
            thedocs = {};
            _ref2 = data.response.docs;
            for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
              d = _ref2[_i];
              thedocs[d.bibcode] = d;
            }
            docnames = (function() {
              var _j, _len1, _ref3, _results;
              _ref3 = data.response.docs;
              _results = [];
              for (_j = 0, _len1 = _ref3.length; _j < _len1; _j++) {
                d = _ref3[_j];
                _results.push(d.bibcode);
              }
              return _results;
            })();
            _results = [];
            for (_j = 0, _len1 = theitems.length; _j < _len1; _j++) {
              d = theitems[_j];
              if (_ref3 = d.basic.name, __indexOf.call(docnames, _ref3) >= 0) {
                e = thedocs[d.basic.name];
              } else {
                e = {};
              }
              _results.push(format_item(plinv.itemviews[d.basic.fqin].$('.searchresultl'), e));
            }
            return _results;
          };
          return syncs.send_bibcodes(config.bq1url, theitems, cb, eb);
        });
      });
    });
  };

  root.postform = {
    do_postform: do_postform
  };

}).call(this);
