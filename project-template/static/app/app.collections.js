
var PostCollection = Backbone.Collection.extend({
  model: Post,
  url: '/post',
  
  by_user: function(username) {
    return this.filter(function(post) {
      return post.get('username') == username;
    });
  },
  
  fetch_single: function(id) {
    console.info("fetch_single:" + id);
    return this.filter(function(post) {
      return post.get('id') == id;
    });
  }
  
});