
var Sketch = Backbone.Router.extend({
  _index: null,
  _posts: null,
  
  collections: {},
  
  views: {},
  
  routes: {
    '': 'index',
    'p/:id': 'post',
    'u/': 'user',
    't': 'tag',
    'new': 'new',
    'refresh': 'refresh',
  },
  
  initialize: function() {
    console.info('Running Sketch');
          
    if(this._index === null) {      
      this._posts = new PostCollection();
      this._index = new PostListView({collection: this._posts});
      this._posts.fetch();
    }

    Backbone.history.start();
    // Backbone.history.start({pushState: true});
    return this;
  },
  
  test: function(what) {
    alert(what);
  },
  
  
  refresh: function() {
    this._posts.fetch();
  },
  
  index: function(id, next) {
    console.info('Index page', id, next);
    this._index.render();
  },
  
  post: function(id) {
    console.info("Post:" + id);
    // this._posts = new PostCollection();
    // this._index = new PostListView({collection: this._posts});
    this._posts.fetch_single(id);
  },
  
  user: function() {
    console.info('User page');
  },
  
  tag: function() {
    console.info('Tag page');
  },
  
  new: function() {
    console.info('new img');
    
  }
});
  