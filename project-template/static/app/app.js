
(function($) {
  
  var Todo = Backbone.Model.extend({
  });
  
  
  var TodoCollection = Backbone.Collection.extend({
    url: '/todo',
    model: Todo
  });
  
  
  var TodoView = Backbone.View.extend({
    tagName: 'li',
    className: 'todo',
    
    events: {
      'dblclick': 'markDone',
      'click div.remove': 'remove',
    },
    
    initialize: function() {
      this.$el = $(this.el);
      _.bindAll(this, 'render', 'unrender', 'remove', 'click', 'toggleDone');
      this.model.view = this;
      this.model.bind('change', this.render);
      this.model.bind('remove', this.unrender);
      this.model.bind('change:done', this.toggleDone);
    },
    
    click: function() {
      console.info('todoview::click');
      this.$el.css('border', '1px solid red');
    },
    
    remove: function() {
      console.info('todoview: remove');
      this.model.destroy({
        success: function() {
          console.info('destroyed');
        },
        error: function() {
          console.info('destroy error');
        }
      });
    },
    
    markDone: function(ev) {
      this.model.set({done: !this.model.get('done')})
      ev.preventDefault();
      console.info(ev);
    },
    
    toggleDone: function(ev) {
      console.info('todoview::toggleDone');
      if(this.model.get('done')) {
        console.info('marking undone');
        this.$el.addClass('done');
        this.$el.css('border', '1px solid red');
      } else {
        console.info('marking done');
        this.$el.removeClass('done');
        this.$el.css('border', '1px solid green');
      }
    },
    
    unrender: function() {
      this.$el.remove();
    },
    
    render: function() {
      var template = "{{ when }} {{ desc }} {{ done }} <div class=\"remove\"> x </div>";
      html = Mustache.to_html(template, this.model.toJSON());
      if(this.model.get('done') == true) {
        $(this.el).addClass('done');
      }
      this.el.innerHTML = html;
      return this;
    }
  });
  
  
  var TodoListView = Backbone.View.extend({
    tagName: 'ul',
    className: 'todolist',
    
    initialize: function() {
      this._todoItems = []
      _.bindAll(this, 'render', 'reset');
      this.collection.bind('reset', this.reset)
      
    },
    
    render: function() {
      var self = this;
      
      _(this._todoItems).each(function(dv) {
        $(self.el).append(dv.render().el);
      })
      return this;
    },
    
    reset: function() {
      var self = this;
      self._todoItems = []
      this.collection.each(function (todo) {
        self._todoItems.push(new TodoView({model: todo}));
      })
      this.render();
    }
  });
  
  
  var TodoApp = Backbone.Router.extend({
    
    routes: {
      '': 'index',
      'list/:id': 'list',
    },
    
    initialize: function(holder) {
      console.info('router::init');
      this.holder = $(holder);
      Backbone.history.start();
    },
    
    index: function() {
      console.info('router::index');
      if(this._index == null) {
        this._todolist = new TodoCollection();
        this._index = new TodoListView({collection: this._todolist});
        this._todolist.fetch();
      }
      this.holder.append(this._index.render().el);
    },
    
    list: function(id) {
      console.info('router::list');
      
    }
  });
  


  
  
  

  
  window.TodoApp = TodoApp;
  
})(Zepto);