# myzhihu
<h3>简介</h3>
<p>这是一个使用<code>Python</code> + <code>Flask</code>， 模仿知乎做的一个小型网站。由于时间和水平有限，很多东西暂时还做得不到位。
不过随着水平的进步，作者会不断优化的。</p>
<h3>网站地址</h3>
<p><a href="https://johushiyu.herokuapp.com/">网站需要登录访问</a></p>
<h3>功能</h3>
<p>
<ul>
<li>注册，登录，设置个人资料</li>
<li>查看话题广场，添加话题</li>
<li>提问，回答问题</li>
<li>关注话题，关注问题，关注其他用户</li>
<li>回复评论，点赞</li>
<li>首页可以查看关注的话题动态，关注人的回答和关注人点赞情况</li>
<li>发现当天最热回答，当月最热回答</li>
<li>关键字搜索回答</li>
<li>更改密码，重设密码，更改邮箱</li>
</ul>
</p>
<h3>本地使用</h3>
<p>clone到本地，安装需要的库</p>
<p><code>$ pip install -r requirements.txt</code></p>
<p>创建数据库，设定角色权限</p>
<p><code>$ python manage.py shell</code></p>
<p><code>$ db.create_all()</code></p>
<p><code>$ Role.insert_roles()</code></p>
<p>运行</p>
<p><code>$ python manage.py runserver</code></p>
<p>打开本地浏览器访问<code>127.0.0.1:5000</code>即可。</p>

