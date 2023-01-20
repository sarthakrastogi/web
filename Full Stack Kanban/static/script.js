
         var app = new Vue({
             el: '#kanbanapp',
             data: {
                 title: '',
                 content: '',
                 deadline: '',
                 completed_flag: '',
                 list_id: '',
                 tasks: ["blank"],
                 new_id: '',
                 new_title: '',
                 new_content: '',
                 new_deadline: '',
                 new_completed_flag: '',
                 new_list_id: '',

                 list_title: '',
                 lists: ["blank"],
                 new_list_list_id: '',
                 new_list_title: '',

                 task: '',
                 list_holding_these_tasks: '',
                 what_to_do: '',
                 list_name_for_deletion: '',
                 //id: '',
                 list_list_id: '',
                 current_list_id: '',
                 list: '',
                 username: 'blank',

             },
             delimiters: ['{','}'],

             methods: {
                 showModal(id) {
                     this.$refs[id].show()
                 },
                 hideModal(id) {
                     this.$refs[id].hide()
                 },

                 task_addition_button(){
                         axios.post("http://127.0.0.1:5000/insert_task/"+this.username,
                             {title : this.title, content : this.content, deadline : this.deadline, completed_flag : this.completed_flag, list_id : this.list_id}
                         )
                         .then(res => {
                             console.log(res)
                             alert('New task added 🫡')
                             this.title = ''
                             this.content = ''
                             this.deadline = ''
                             this.completed_flag = ''
                             this.list_id = ''

                             app.hideModal('task-creation')
                             app.getTasks()
                         })
                 },

                 async getTasks(){
                      let result = await axios({
                        url: 'http://localhost:5000/user',
                        method: 'get'
                      }).then(res => {
                        return res.data.username
                      })
                      this.username = result
                   username = this.username
                     axios({
                       url: 'http://localhost:5000/fetch/'+username,
                       method: 'get'
                     })
                     .then(res => {
                       this.tasks = res.data.tasks
                       this.lists = res.data.lists
                     })

                 },

                 editTask(id){
                     console.log(id)
                     axios.get("http://127.0.0.1:5000/edit_task/" + id + "/" + this.username)
                     .then(res => {
                         console.log(res.data)
                         this.new_id = res.data.editmember['id']
                         this.new_title = res.data.editmember['title']
                         this.new_content = res.data.editmember['content']
                         this.new_deadline = res.data.editmember['deadline']
                         this.new_completed_flag = res.data.editmember['completed_flag']
                         this.new_list_id = res.data.editmember['list_id']
                         app.showModal('task-updation')
                     })
                 },

                 onUpdateTask(){
                         axios.post("http://127.0.0.1:5000/update_task/" + this.username,
                             { new_id : this.new_id, new_title : this.new_title, new_content : this.new_content, new_deadline : this.new_deadline, new_completed_flag : this.new_completed_flag, new_list_id : this.new_list_id}
                         )
                         .then(res => {
                             console.log(res)
                             this.new_title = '';
                             this.new_content = '';
                             this.new_deadline = '';
                             this.new_completed_flag = '';
                             this.new_list_id = '';
                             this.new_id = '';

                             app.hideModal('task-updation');
                             app.getTasks();
                         })
                 },

                 deleteTask(id){
                     if (window.confirm('Are you sure you want to delete this task?')) {
                         axios.get("http://127.0.0.1:5000/delete_task/" + id + "/" + this.username)
                         .then(res => {
                             console.log(res)
                             alert('The task is gone 😮‍💨')
                             app.getTasks();
                         })
                     }
                 },

                 exportTask(id){
                     if (window.confirm('Export this task')) {
                         axios.get("http://127.0.0.1:5000/export_task/" + id)
                         .then(res => {
                             console.log(res)
                             alert('The task has been exported to a csv 😉')
                             app.getTasks();
                         })
                     }
                 },

             list_addition_button(){

                     axios.post("http://127.0.0.1:5000/insert_list/"+this.username,
                         {list_title : this.list_title}
                     )
                     .then(res => {
                         console.log(res)
                         alert('New list up and running 😗')
                         //this.list_list_id = ''
                         this.list_title = ''

                         app.hideModal('list-creation')
                         app.getTasks()
                     })
             },

             editList(list_list_id){
                 console.log(list_list_id)
                 axios.get("http://127.0.0.1:5000/edit_list/" + list_list_id + "/"+ this.username)
                 .then(res => {
                     console.log(res.data)
                     this.new_list_list_id = res.data.editmember['list_list_id']
                     this.new_list_title = res.data.editmember['list_title']
                     app.showModal('list-updation')
                 })
             },

             onUpdateList(){
                     axios.post("http://127.0.0.1:5000/update_list/" + this.username,
                         {new_list_title : this.new_list_title, current_list_id : this.current_list_id}
                     )
                     .then(res => {
                         console.log(res)
                         //this.new_list_list_id = '';
                         this.new_list_title = '';
                         app.hideModal('list-updation');
                         app.getTasks();
                     })
             },


             deleteList(list_list_id){
                 console.log(list_list_id)
                 axios.get("http://127.0.0.1:5000/delete_list/" + list_list_id + "/" + this.username)
                 .then(res => {
                     console.log(res.data)
                     this.new_list_list_id = res.data.editmember['list_list_id']
                     this.new_list_title = res.data.editmember['list_title']
                     app.showModal('list-deletion')
                 })
             },


             onDeleteList(){
                     axios.post("http://127.0.0.1:5000/pre_delete_list/" + this.username,
                         {list_name_for_deletion : this.list_name_for_deletion, what_to_do : this.what_to_do, list_holding_these_tasks : this.list_holding_these_tasks}
                     )
                     .then(res => {
                         console.log(res)
                         //this.new_list_list_id = '';
                         this.new_list_title = '';
                         this.list_name_for_deletion = '';
                         this.what_to_do = '';
                         this.list_holding_these_tasks = '';

                         app.hideModal('list-deletion');
                         app.getTasks();
                     })
             },

             deleteList22(list_list_id){
                 if (window.confirm('Delete this list?')) {
                     axios.get("http://127.0.0.1:5000/delete_list/" + list_list_id + "/" + this.username)
                     .then(res => {
                         console.log(res)
                         alert('That list is gone 🤯')
                         app.getTasks();
                     })
                 }
             },

             exportAll(){
                     axios.get("http://127.0.0.1:5000/export_all/" + this.username)
                     .then(res => {
                         console.log(res)
                         alert('The lists have been exported to a csv 😉')
                         app.getTasks();
                 })
             },

             showReport(){
                     axios.get("http://127.0.0.1:5000/plots/" + this.username)
                     window.open("http://127.0.0.1:5000/plots/" + this.username);

             },
         },
             mounted: function(){
               this.getTasks()
             }
         })
