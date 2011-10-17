  Sketch.View = Backbone.View.extend({
    template: function() {
      
    }
  });
  

var PostView = Sketch.View.extend({
  
  className: 'post',

  events: {
    'click a.comments': 'comments'
  },
  
  initialize: function() {
    _.bindAll(this, 'render', 'comments');
    this.model.view = this;
  },
  
  render: function() {
    var template = "<div class=\"usericon\"> \
        <img src=\"{{ user_picture }}\"> \
      </div> \
      <div class=\"postimage\"> \
        <img src=\"{{ img_url }}\" class=\"postimg\"> \
      </div> \
      <div class=\"postdata\"> \
        <p><a href=\"/{{ username}}\" class=\"username\">{{ username }}</a></p> \
        <p class=\"msg\">{{ msg }}</p> \
        <p class=\"meta\">{{ updated.ctime }} <a href=\"#p/{{ id }}\">remix</a> <a href=\"#\" class=\"comments\">12 comments</a> <a href=\"/#p/{{ id }}\">#</a></p> \
      </div>";
    // html = Mustache.to_html(template, this.model.toJSON());
    this.el.innerHTML = Mustache.to_html(template, this.model.toJSON());
    // $(this.el).html(html);
    return this;
  },
  
  comments: function(ev) {
    ev.preventDefault();
    return false;
  }
});


var PostListView = Backbone.View.extend({
  
  events: {
    
  },
  
  initialize: function() {
    var self = this;
    
    this._postViews = [];
    _.bindAll(this, 'render', 'updatePosts', 'reset');
    
    this.collection.each(function (post) {
      console.info(post);
      self._postViews.push(new PostView({model: post}));
    });
    
    
    this.collection.bind('all', this.updatePosts);
    this.collection.bind('reset', this.reset);
  },
  
  updatePosts: function(ez) {
    console.info('updatePosts', ez);
  },
  
  reset: function() {
    var self = this;
    console.info("PostLiveView::reset");
    
    self._postViews = [];
    this.collection.each(function (post) {
      console.info(post);
      self._postViews.push(new PostView({model: post}));
    });
    this.render();
  },
  
  render: function() {
    var self = this;

    _(this._postViews).each(function(dv) {
      $(self.el).append(dv.render().el);
    });
          
    $('#ptl').html(null).append(this.el);
    
    return this;
  }
});

