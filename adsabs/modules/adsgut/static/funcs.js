// Generated by CoffeeScript 1.7.1
(function() {
  var $, AddGroup, CreatePostable, InviteUser, MakePublic, br, dd, dl, dt, email_split, format_item, format_notes_for_item, format_postings_for_item, format_row, format_tags, format_tags_for_item, get_groups, get_taggings, get_tags, group_info_template, group_itemsinfo_template, li, library_info_template, library_itemsinfo_template, monthNamesShort, parse_fortype, parse_fqin, postable_info, postable_info_layout, postable_info_layout2, postable_inviteds, postable_inviteds_template, prefix, raw, renderable, root, rwmap, short_authors, strong, this_postable, time_format, ul, w,
    __hasProp = {}.hasOwnProperty,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  $ = jQuery;

  renderable = teacup.renderable, ul = teacup.ul, li = teacup.li, dl = teacup.dl, dt = teacup.dt, dd = teacup.dd, raw = teacup.raw, br = teacup.br, strong = teacup.strong;

  w = widgets;

  prefix = GlobalVariables.ADS_PREFIX + "/adsgut";

  monthNamesShort = {
    '00': "",
    '01': "Jan",
    '02': "Feb",
    '03': "Mar",
    '04': "Apr",
    '05': "May",
    '06': "Jun",
    '07': "Jul",
    '08': "Aug",
    '09': "Sep",
    '10': "Oct",
    '11': "Nov",
    '12': "Dec"
  };

  short_authors = function(authors) {
    var n;
    if (authors.length <= 4) {
      return authors.slice(0, 4).join('; ');
    } else {
      n = authors.length - 4;
      return authors.slice(0, 4).join('; ') + (" <em>and " + n + " coauthors</em>");
    }
  };

  parse_fqin = function(fqin) {
    var vals;
    vals = fqin.split(':');
    return vals[-1 + vals.length];
  };

  format_item = function($sel, iteminfo) {
    var author, leave, month, pubdate, title, year, _ref, _ref1, _ref2, _ref3;
    _ref = iteminfo.pubdate ? iteminfo.pubdate.split('-') : [void 0, void 0, void 0], year = _ref[0], month = _ref[1], leave = _ref[2];
    if (month === void 0) {
      pubdate = year != null ? year : "unknown";
    } else {
      pubdate = (_ref1 = monthNamesShort[month] + " " + year) != null ? _ref1 : "unknown";
    }
    $sel.append("<span class='pubdate pull-right'><em>published in " + pubdate + "</em></span><br/>");
    title = (_ref2 = iteminfo.title) != null ? _ref2 : "No title found";
    $sel.append("<span class='title'><strong>" + title + "</strong></span><br/>");
    author = (_ref3 = iteminfo.author) != null ? _ref3 : ['No authors found'];
    return $sel.append("<span class='author'>" + (short_authors(author)) + "</span>");
  };

  format_tags = function(tagtype, $sel, tags, tagqkey) {
    var htmlstring, k, nonqloc, t, typestring, url, urla, v, _i, _len, _ref;
    $sel.empty();
    typestring = tagtype.split(':')[1];
    htmlstring = "<li class=\"nav-header\">Filter by: " + typestring + "</li>";
    for (_i = 0, _len = tags.length; _i < _len; _i++) {
      _ref = tags[_i], k = _ref[0], v = _ref[1];
      if (tagqkey === 'stags') {
        t = v[0];
      } else if (tagqkey === 'tagname') {
        t = k;
      } else {
        t = "CRAP";
      }
      nonqloc = document.location.href.split('?')[0];
      if (tagqkey === 'tagname') {
        url = nonqloc + ("?query=tagtype:" + tagtype + "&query=" + tagqkey + ":" + t);
        urla = document.location + ("&query=tagtype:" + tagtype + "&query=" + tagqkey + ":" + t);
        if (nonqloc === document.location.href) {
          urla = document.location + ("?query=tagtype:" + tagtype + "&query=" + tagqkey + ":" + t);
        }
      } else {
        url = nonqloc + ("?query=" + tagqkey + ":" + t);
        urla = document.location + ("&query=" + tagqkey + ":" + t);
        if (nonqloc === document.location.href) {
          urla = document.location + ("?query=" + tagqkey + ":" + t);
        }
      }
      htmlstring = htmlstring + ("<li><span><a href=\"" + url + "\">" + k + "</a>&nbsp;<a href=\"" + urla + "\">(+)</a></span></li>");
    }
    return $sel.html(htmlstring);
  };

  time_format = function(timestring) {
    var d, t, _ref;
    _ref = timestring.split('.')[0].split('T'), d = _ref[0], t = _ref[1];
    d = d.split('-').slice(1, 3).join('/');
    t = t.split(':').slice(0, 2).join(':');
    return d + " " + t;
  };

  email_split = function(e) {
    var hfp, host, name, _ref;
    _ref = e.split('@'), name = _ref[0], host = _ref[1];
    hfp = host.split('.')[0];
    return name + '@' + hfp;
  };

  this_postable = function(pval, pview) {
    var pble;
    if (pview !== 'udg' && pview !== 'none') {
      if (pval === true) {
        return pble = "<i class='icon-comment'></i>&nbsp;&nbsp;";
      } else {
        return pble = '';
      }
    } else {
      pble = '';
      return pble;
    }
  };

  format_row = function(noteid, notetext, notemode, notetime, user, currentuser, truthiness, pview) {
    var lock, nmf, nt, outstr, tf, uf;
    tf = time_format(notetime);
    uf = user === currentuser ? 'me' : email_split(user);
    lock = "<i class='icon-lock'></i>&nbsp;&nbsp;";
    nmf = notemode === '1' ? lock : '';
    nt = this_postable(truthiness, pview);
    outstr = "<tr><td style='white-space: nowrap;'>" + tf + "</td><td style='text-align: right;'>" + uf + "&nbsp;&nbsp;</td><td>" + nmf + nt + "</td><td class='notetext'>" + notetext + "</td>";
    if (uf === 'me') {
      outstr = outstr + '<td><btn style="cursor:pointer;" class="removenote" id="' + noteid + '"><i class="icon-remove-circle"></i></btn></td></tr>';
    } else {
      outstr = outstr + "<td></td></tr>";
    }
    return outstr;
  };

  format_notes_for_item = function(fqin, notes, currentuser, pview) {
    var end, lock, start, t, t3list;
    start = '<table class="table-condensed table-striped">';
    end = "</table>";
    lock = "<i class='icon-lock'></i>&nbsp;&nbsp;";
    t3list = (function() {
      var _i, _len, _ref, _results;
      _ref = notes[fqin];
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        t = _ref[_i];
        _results.push(format_row(t[5], t[0], t[3], t[1], t[2], currentuser, t[6], pview));
      }
      return _results;
    })();
    if (t3list.length > 0) {
      return start + t3list.join("") + end;
    } else {
      return start + end;
    }
  };

  format_tags_for_item = function(fqin, stags, memberable, tagajax) {
    var t, t2list;
    if (tagajax == null) {
      tagajax = true;
    }
    t2list = (function() {
      var _i, _len, _ref, _results;
      _ref = stags[fqin];
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        t = _ref[_i];
        _results.push({
          url: "" + prefix + "/postable/" + memberable.nick + "/group:default/filter/html?query=tagname:" + t[0] + "&query=tagtype:" + t[1],
          text: "" + t[0],
          id: "" + t[0],
          by: tagajax ? memberable.adsid === t[2] : false
        });
      }
      return _results;
    })();
    if (t2list.length > 0) {
      return t2list;
    } else {
      return [];
    }
  };

  parse_fortype = function(fqin) {
    var vals, vals2;
    vals = fqin.split(':');
    vals2 = vals[-2 + vals.length].split('/');
    return vals2[-1 + vals2.length];
  };

  format_postings_for_item = function(fqin, postings, nick) {
    var p, p2list, postingslist, priv, publ;
    postingslist = _.uniq(postings[fqin]);
    publ = "adsgut/group:public";
    priv = "" + nick + "/group:default";
    p2list = (function() {
      var _i, _len, _results;
      _results = [];
      for (_i = 0, _len = postingslist.length; _i < _len; _i++) {
        p = postingslist[_i];
        if (p !== publ && p !== priv && parse_fortype(p) !== "app") {
          _results.push("<a href=\"" + prefix + "/postable/" + p + "/filter/html\">" + (parse_fqin(p)) + "</a>");
        }
      }
      return _results;
    })();
    if (p2list.length > 0) {
      return p2list;
    } else {
      return [];
    }
  };

  get_tags = function(tags, tqtype) {
    var fqtn, k, name, t, tdict, type, user, v, _i, _len;
    tdict = {};
    if (tqtype === 'stags') {
      return (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = tags.length; _i < _len; _i++) {
          t = tags[_i];
          _results.push([t[3], [t[0]]]);
        }
        return _results;
      })();
    }
    for (_i = 0, _len = tags.length; _i < _len; _i++) {
      t = tags[_i];
      fqtn = t[0], user = t[1], type = t[2], name = t[3];
      if (tdict[name] === void 0) {
        tdict[name] = [];
      }
      tdict[name].push(fqtn);
    }
    if (tqtype === 'tagname') {
      return (function() {
        var _results;
        _results = [];
        for (k in tdict) {
          if (!__hasProp.call(tdict, k)) continue;
          v = tdict[k];
          _results.push([k, v]);
        }
        return _results;
      })();
    }
    return [];
  };

  get_taggings = function(data) {
    var combi, e, k, notes, stags, td, tg, tp, tp2, v, _ref;
    stags = {};
    notes = {};
    _ref = data.taggings;
    for (k in _ref) {
      if (!__hasProp.call(_ref, k)) continue;
      v = _ref[k];
      tp = data.taggingtp[k];
      td = data.taggingsdefault[k];
      tg = v[1];
      tp2 = (function() {
        var _i, _len, _ref1, _results;
        _ref1 = _.zip(tp, td);
        _results = [];
        for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
          e = _ref1[_i];
          _results.push(e[0] || e[1]);
        }
        return _results;
      })();
      combi = _.zip(tg, tp2, tp);
      if (v[0] > 0) {
        if (data.fqpn === null || data.fqpn === void 0) {
          stags[k] = (function() {
            var _i, _len, _results;
            _results = [];
            for (_i = 0, _len = combi.length; _i < _len; _i++) {
              e = combi[_i];
              if (e[0].posting.tagtype === "ads/tagtype:tag") {
                _results.push([e[0].posting.tagname, e[0].posting.tagtype, e[0].posting.postedby]);
              }
            }
            return _results;
          })();
          notes[k] = (function() {
            var _i, _len, _results;
            _results = [];
            for (_i = 0, _len = combi.length; _i < _len; _i++) {
              e = combi[_i];
              if (e[0].posting.tagtype === "ads/tagtype:note") {
                _results.push([e[0].posting.tagdescription, e[0].posting.whenposted, e[0].posting.postedby, e[0].posting.tagmode, e[1], e[0].posting.tagname, e[2]]);
              }
            }
            return _results;
          })();
        } else {
          stags[k] = (function() {
            var _i, _len, _results;
            _results = [];
            for (_i = 0, _len = combi.length; _i < _len; _i++) {
              e = combi[_i];
              if (e[0].posting.tagtype === "ads/tagtype:tag" && e[1] === true) {
                _results.push([e[0].posting.tagname, e[0].posting.tagtype, e[0].posting.postedby]);
              }
            }
            return _results;
          })();
          notes[k] = (function() {
            var _i, _len, _results;
            _results = [];
            for (_i = 0, _len = combi.length; _i < _len; _i++) {
              e = combi[_i];
              if (e[0].posting.tagtype === "ads/tagtype:note" && e[1] === true) {
                _results.push([e[0].posting.tagdescription, e[0].posting.whenposted, e[0].posting.postedby, e[0].posting.tagmode, e[1], e[0].posting.tagname, e[2]]);
              }
            }
            return _results;
          })();
        }
      } else {
        stags[k] = [];
        notes[k] = [];
      }
    }
    return [stags, notes];
  };

  get_groups = function(nick, cback) {
    return $.get("" + prefix + "/user/" + nick + "/groupsuserisin", function(data) {
      var groups;
      groups = data.groups;
      return cback(groups);
    });
  };

  rwmap = function(boolrw) {
    if (boolrw === true) {
      return "read and post";
    } else {
      return "read only";
    }
  };

  postable_inviteds_template = renderable(function(fqpn, users, scmode) {
    var k, namedict, userlist, v;
    if (scmode == null) {
      scmode = false;
    }
    userlist = (function() {
      var _results;
      _results = [];
      for (k in users) {
        v = users[k];
        _results.push(v[0]);
      }
      return _results;
    })();
    if (scmode) {
      userlist = (function() {
        var _results;
        _results = [];
        for (k in users) {
          v = users[k];
          _results.push(v[0]);
        }
        return _results;
      })();
      if (userlist.length === 0) {
        userlist = ['No Invitations Yet'];
      }
      return w.one_col_table("Invited Users", userlist);
    } else {
      if (userlist.length === 0) {
        users = {
          'No Invitations Yet': ['No Invitations Yet', '']
        };
      }
      namedict = {};
      for (k in users) {
        namedict[users[k][0]] = rwmap(users[k][1]);
      }
      return w.table_from_dict("Invited User", "Access", namedict);
    }
  });

  postable_inviteds = function(fqpn, data, template, scmode) {
    if (scmode == null) {
      scmode = false;
    }
    return template(fqpn, data.users, scmode);
  };

  postable_info_layout = renderable(function(isowner, _arg, oname, cname, mode) {
    var a, basic, description, dtext, modetext, nick, owner, url;
    basic = _arg.basic, owner = _arg.owner, nick = _arg.nick;
    if (mode == null) {
      mode = "filter";
    }
    description = basic.description;
    if (description === "") {
      description = "not provided";
    }
    if (isowner) {
      dtext = w.editable_text(description);
    } else {
      dtext = description;
    }
    if (mode === "filter") {
      modetext = "Link";
    } else if (mode === "profile") {
      modetext = "Info";
    }
    url = "" + prefix + "/postable/" + basic.fqin + "/" + mode + "/html";
    a = "&nbsp;&nbsp;<a href=\"" + url + "\">" + basic.name + "</a>";
    return dl('.dl-horizontal', function() {
      dt("Description");
      dd(function() {
        return raw(dtext);
      });
      dt("Owner");
      dd(oname);
      dt("Creator");
      dd(cname);
      dt("Created on");
      dd(basic.whencreated);
      dt("" + modetext + ":");
      return dd(function() {
        return raw(a);
      });
    });
  });

  postable_info_layout2 = renderable(function(_arg, oname, cname, mode) {
    var a, basic, modetext, nick, owner, url;
    basic = _arg.basic, owner = _arg.owner, nick = _arg.nick;
    if (mode == null) {
      mode = "profile";
    }
    if (mode === "filter") {
      modetext = "Link";
    } else if (mode === "profile") {
      modetext = "Info/Admin";
    }
    url = "" + prefix + "/postable/" + basic.fqin + "/" + mode + "/html";
    a = "&nbsp;&nbsp;<a href=\"" + url + "\">" + basic.name + "</a>";
    return dl('.dl-horizontal', function() {
      dt("Owner");
      dd(oname);
      dt("" + modetext + ":");
      return dd(function() {
        return raw(a);
      });
    });
  });

  library_info_template = renderable(function(isowner, data) {
    return postable_info_layout(isowner, data.library, data.oname, data.cname);
  });

  group_info_template = renderable(function(isowner, data) {
    return postable_info_layout(isowner, data.group, data.oname, data.cname);
  });

  library_itemsinfo_template = renderable(function(isowner, data) {
    return postable_info_layout(isowner, data.library, data.oname, data.cname, "profile");
  });

  group_itemsinfo_template = renderable(function(isowner, data) {
    return postable_info_layout(isowner, data.group, data.oname, data.cname, "profile");
  });

  postable_info = function(isowner, data, template) {
    return template(isowner, data);
  };

  InviteUser = (function(_super) {
    __extends(InviteUser, _super);

    function InviteUser() {
      this.inviteUserEH = __bind(this.inviteUserEH, this);
      this.render = __bind(this.render, this);
      return InviteUser.__super__.constructor.apply(this, arguments);
    }

    InviteUser.prototype.tagName = 'div';

    InviteUser.prototype.events = {
      "click .sub": "inviteUserEH"
    };

    InviteUser.prototype.initialize = function(options) {
      this.withcb = options.withcb, this.postable = options.postable;
      if (this.withcb) {
        return this.content = widgets.one_submit_with_cb("Invite a user using their email:", "Invite", "Can Post?");
      } else {
        return this.content = widgets.one_submit("Invite a user using their email:", "Invite");
      }
    };

    InviteUser.prototype.render = function() {
      this.$el.html(this.content);
      return this;
    };

    InviteUser.prototype.inviteUserEH = function() {
      var adsid, cback, changerw, eback, loc, rwmode;
      loc = window.location;
      cback = function(data) {
        return window.location = location;
      };
      eback = function(xhr, etext) {
        return alert("Did not succeed: " + etext);
      };
      changerw = false;
      if (this.withcb) {
        rwmode = this.$('.cb').is(':checked');
        if (rwmode) {
          changerw = true;
        } else {
          changerw = false;
        }
      }
      adsid = this.$('.txt').val();
      return syncs.invite_user(adsid, this.postable, changerw, cback, eback);
    };

    return InviteUser;

  })(Backbone.View);

  MakePublic = (function(_super) {
    __extends(MakePublic, _super);

    function MakePublic() {
      this.makePublic = __bind(this.makePublic, this);
      this.render = __bind(this.render, this);
      return MakePublic.__super__.constructor.apply(this, arguments);
    }

    MakePublic.prototype.tagName = 'div';

    MakePublic.prototype.events = {
      "click .sub": "makePublic"
    };

    MakePublic.prototype.initialize = function(options) {
      var url;
      this.postable = options.postable, this.users = options.users;
      this.ispublic = false;
      if (this.users['adsgut/group:public'] != null) {
        this.ispublic = true;
      }
      if (this.ispublic) {
        url = "" + prefix + "/postable/" + this.postable + "/filter/html";
        return this.content = "<p><a class='btn btn-info' href='" + url + "'>PUBLIC LINK</a></p>";
      } else {
        return this.content = widgets.zero_submit("Clicking this will enable anyone to see this library (they cant write to it):", "Make Public");
      }
    };

    MakePublic.prototype.render = function() {
      this.$el.html(this.content);
      return this;
    };

    MakePublic.prototype.makePublic = function() {
      var cback, cback2, eback, loc;
      loc = window.location;
      cback2 = (function(_this) {
        return function(data) {
          return window.location = location;
        };
      })(this);
      cback = (function(_this) {
        return function(data) {
          return syncs.add_group('adsgut/group:public', _this.postable, false, cback2, eback);
        };
      })(this);
      eback = function(xhr, etext) {
        return alert("Did not succeed: " + etext);
      };
      return syncs.make_public(this.postable, cback, eback);
    };

    return MakePublic;

  })(Backbone.View);

  AddGroup = (function(_super) {
    __extends(AddGroup, _super);

    function AddGroup() {
      this.addGroupEH = __bind(this.addGroupEH, this);
      this.render = __bind(this.render, this);
      return AddGroup.__super__.constructor.apply(this, arguments);
    }

    AddGroup.prototype.tagName = 'div';

    AddGroup.prototype.events = {
      "click .sub": "addGroupEH"
    };

    AddGroup.prototype.initialize = function(options) {
      var g, _i, _len, _ref;
      this.withcb = options.withcb, this.postable = options.postable, this.groups = options.groups;
      this.groupnames = {};
      _ref = this.groups;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        g = _ref[_i];
        this.groupnames[g] = parse_fqin(g);
      }
      if (this.withcb) {
        return this.content = widgets.dropdown_submit_with_cb(this.groups, this.groupnames, "Add a group you are a member of:", "Add", "Can Post?");
      } else {
        return this.content = widgets.dropdown_submit(this.groups, this.groupnames, "Add a group you are a member of:", "Add");
      }
    };

    AddGroup.prototype.render = function() {
      if (this.groups.length === 0) {
        this.$el.html(this.content);
        this.$(":input").attr("disabled", true);
        this.$el.append("<p class='text-error'>You are not a member of any group. Create some groups first.</p>");
      } else {
        this.$el.html(this.content);
      }
      return this;
    };

    AddGroup.prototype.addGroupEH = function() {
      var cback, changerw, eback, groupchosen, loc, rwmode;
      loc = window.location;
      cback = function(data) {
        return window.location = location;
      };
      eback = function(xhr, etext) {
        return alert("Did not succeed: " + etext);
      };
      changerw = false;
      if (this.withcb) {
        rwmode = this.$('.cb').is(':checked');
        if (rwmode) {
          changerw = true;
        } else {
          changerw = false;
        }
      }
      groupchosen = this.$('.sel').val();
      return syncs.add_group(groupchosen, this.postable, changerw, cback, eback);
    };

    return AddGroup;

  })(Backbone.View);

  CreatePostable = (function(_super) {
    __extends(CreatePostable, _super);

    function CreatePostable() {
      this.createPostableEH = __bind(this.createPostableEH, this);
      this.render = __bind(this.render, this);
      return CreatePostable.__super__.constructor.apply(this, arguments);
    }

    CreatePostable.prototype.tagName = 'div';

    CreatePostable.prototype.events = {
      "click .sub": "createPostableEH"
    };

    CreatePostable.prototype.initialize = function(options) {
      this.postabletype = options.postabletype;
      return this.content = widgets.two_submit("Create a new " + this.postabletype, "Description", "Create");
    };

    CreatePostable.prototype.render = function() {
      this.$el.html(this.content);
      return this;
    };

    CreatePostable.prototype.createPostableEH = function() {
      var cback, eback, loc, postable;
      loc = window.location;
      cback = function(data) {
        return window.location = location;
      };
      eback = function(xhr, etext) {
        return alert("Did not succeed: " + etext);
      };
      postable = {};
      postable.name = this.$('.txt1').val();
      postable.description = this.$('.txt2').val();
      return syncs.create_postable(postable, this.postabletype, cback, eback);
    };

    return CreatePostable;

  })(Backbone.View);

  root.get_tags = get_tags;

  root.get_taggings = get_taggings;

  root.format_item = format_item;

  root.format_tags = format_tags;

  root.get_groups = get_groups;

  root.format_row = format_row;

  root.format_postings_for_item = format_postings_for_item;

  root.format_notes_for_item = format_notes_for_item;

  root.format_tags_for_item = format_tags_for_item;

  root.views = {
    library_info: postable_info,
    group_info: postable_info,
    postable_inviteds: postable_inviteds,
    InviteUser: InviteUser,
    MakePublic: MakePublic,
    AddGroup: AddGroup,
    CreatePostable: CreatePostable
  };

  root.templates = {
    library_info: library_info_template,
    group_info: group_info_template,
    library_itemsinfo: library_itemsinfo_template,
    group_itemsinfo: group_itemsinfo_template,
    postable_inviteds: postable_inviteds_template
  };

}).call(this);
