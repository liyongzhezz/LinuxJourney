[数据表之间的关系](#数据表之间的关系)

[数据表结构](#数据表结构)

[修改数据](#修改数据)

[删除数据](#删除数据)

[单表查找数据](#单表查找数据)

 [外键关系字段添加数据](#外键关系字段添加数据)

[一对多外键关联查询](#一对多外键关联查询)

[多对多插入数据](#多对多插入数据)

[多对多删除数据](#多对多删除数据)

[聚合函数](#聚合函数)

[分组](#分组)

[F查询和Q查询](#F查询和Q查询)



django中使用ORM操作数据库，其通过实例对象语法，将数据表映射成类，数据记录映射成对象，字段映射称为对象属性，从而可以很方便的操作数据库进行增删改查操作，省去了写复杂sql语句的麻烦。



# 数据表之间的关系

数据表间有如下的几种关系：

- 一对一：A表中的一条记录只能在B表中找到唯一一条与之形成对应关系，反之亦然。
- 一对多：A表中的一条记录可以在B表中找到多条记录与之对应，B表中一条记录只对应A中的一条记录。
- 多对多：A表中的一条记录可以对应B中的多条记录，反之亦然。

> 一般情况下，一对一关系在一张表中就可以完成了，而多对多关系则需要一个中间表。



# 数据表结构

**下面都是以这个 书籍-出版社-作者 三个数据表的结构为基础进行的举例**



```python
class Book(models.Model):
  	"""书籍信息表"""
    name = models.CharField(max_length=20)
    price = models.IntegerField()
    pub_date = models.DateField()
    publish = models.ForeignKey("Publish", on_delete=models.SET_NULL, null=True, blank=True)
    authors = models.ManyToManyField("Author")
    
class Publish(models.Model):
    """出版社信息表"""
    name = models.CharField(max_length=32)
    city = models.CharField(max_length=16, default="北京")
    
class Author(models.Model):
    """作者信息表"""
    name = models.CharField(max_length=32)
    age = models.IntegerField(default=20)
```

其中，Book表和Publish表是一个一对多关系，通过外键publish关联，Book表和Author表是一个多对多关系，通过authors字段设置了一个 ManyToMany关系，这样django将会自动创建一个第三张表`book_authors`表。

> 在django创建表的过程就省略了



#向单张表添加数据

**这里先忽略外键关系，单纯说一下如何添加数据，具体多表数据添加后面会说**

ORM将表抽象为类，字段抽象为属性，所以实例化一个类然后对属性赋值就可以实现表数据插入了，例如：

```python
book = Book(name='python基础', price=99, author='lee', pub_date='2019-12-22')
book.save()
```



这种方式在最后需要调用`save`方法来保存数据，django提供了一种更简便的方式：

```python
Book.objects.create(name='java基础', price=99, author='pete', pub_date='2019-12-22')

# 或者将字段单独保存到字典中，注意args前边的两个星号
args = {'name': 'php基础', 'price': 99, 'author': 'pete', 'pub_date': '2019-12-22'}
Book.objects.create(**args)
```



# 修改数据

修改数据同样有两种方式，第一种是获取到待修改数据对象，然后修改其中的某一个属性值：

```python
b = Book.objects.get(author='lee')
b.price = 12
b.save()
```

> 这种方式效率不高，因为实际执行的sql其实修改了所有的字段。



效率更高的方式是使用update方法进行修改，只修改了需要修改的字段：

```python
Book.objects.filter(author='lee').update(price=100)
```



# 删除数据

删除数据比较简单，找到指定的数据后使用del方法删除即可：

```python
Book.objects.filter(author='lee').delete()
```



# 单表查找数据

查询表中所有的数据可以使用all方法：

```python
Book.objects.all()
```



查询结果是QuerySet类型（对象集合），对它可以进行切片操作，例如：

```python
Book.objects.all()[:3]
book_list = Book.objects.all()[::-1]
```



查询第一条和最后一条可以使用first和last方法，例如：

```python
Book.objects.first()
ook.objects.first()
```



也可以使用filter活get方法进行条件筛选，例如：

```python
Book.objects.filter(id=3)
Book.objects.get(id=4)
```

> 两者的区别是：filter的结果是一个QuerySet，可对其进行遍历，而get结果是一个对象，不可遍历；get结果只能有一个，查到多个或者没查到都会报错；



使用values活values_list方法可以只去查询结果中的部分属性(字段)值，例如：

```python
Book.objects.filter(author='lee').values("name", "price")
Book.objects.filter(author='lee').values_list("name", "price")
```

> 区别是：values返回的QuerySet中的元素是字典，而values_list返回的QuerySet中的元素是元组。



查询不配条件的数据，使用exclude方法，例如：

```python
Book.objects.exclude(author='pete')
```



获取到的数据进行排序，使用order_by或reverse方法：

```python
# 按照price字段排序，默认从小到大
Book.objects.all().order_by('price')

# 反向排序
Book.objects.all().reverse()
```



使用distinct方法可以进行去重：

```python
Book.objects.all().values('author').distinct()
```

> 注意，这个方法必须在使用values后使用，如果在all后使用则无法去重，因为有自增id存在，则每一个数据都是不同的(尽管字段都相同)



统计查询个数可以使用count方法：

```python
Book.objects.all().count()
```



django还支持双下划线进行模糊匹配，类似于sql中的like语句：

```python
# 查询价格大于50的书籍
Book.objects.filter(price__gt=50)
# 查询名称包含p的书籍，icontains不区分大小写，contains区分大小写
Book.objects.filter(name__icontains='p')
# 查询价格为99元或12元之间的书籍
Book.objects.filter(price__in=[99, 12])
# 查询价格不是99元或12元的书籍
Book.objects.exclude(price__in=[99, 12])
# 查询价格在50到100范围内的书籍并按照价格排序
Book.objects.filter(price__range=[50, 100]).order_by('price')
```



# 外键关系字段添加数据

在数据表定义中，Book表中的publish和Publish表是一个外键关系，那么此时在Book表中插入数据可以这样做：

```python
# 插入一本A出版社出版的书，首先查到A出版社对象
publish_obj = Publish.objects.get(name='A')

# 然后将对象赋给Book外键字段
book_info = {'name': 'LINUX', 'price': 998, 'author': 'mike', 'pub_date': '2019-10-01', 'publish': publish_obj}
Book.objects.create(**book_info)
```



# 一对多外键关联查询

还是Book表和Publish表之间关联查询，可以通过Book表中的外键，查询到其所属的出版社信息，例如：

```python
# 方式一
# 首先查询到一条book的对象
book_obj = Book.objects.get(name="go")
# 获取book的属性
book_obj.name  # 书籍名称
book_obj.price  # 书籍价格
# 通过外键获取其对应Publish的信息
book_obj.publish.name  # publish是外建名
```



```python
# 方式二，利用外键查找
Publish.objects.filter(book__name='go').values('name', 'city')
# 或者
Book.objects.filter(name='go').values("publish__name")
```

> 利用了双下划线，其中book为表名



```python
# 某个时间段内的书的出版社信息
Book.objects.filter(pub_date__gt='2019-12-01', pub_date__lt='2019-12-31').values("publish__name")
```



也可以反向查询，通过出版社的对象查询到出版社出版的书：

```python
# 方式一，先查询指定出版社对象，再将对象赋值到Book表的外键中查询
publish_obj = Publish.objects.get(name="A")
book_obj = Book.objects.filter(publish=publish_obj).values('name', 'price')
```



```python
# 方式二，通过 _set方式进行查找
publish_obj = Publish.objects.get(name="cctv")
publish_obj.book_set.all()
```

> 这种方式中book为表名



```python
# 方式三，利用外键查找
Book.objects.filter(publish__name='A').values('name', 'price')
```

> 利用了双下划线，其中publish为外键名称



# 多对多插入数据

如果是使用ManyToMany字段创建的多对多关系，中间表是自动生成的，没法用ORM直接插入数据。但可以通过ManyToMany字段赋值来实现绑定多对多关系。



Book和Auhtor表是一个多对多关系，例如插入某一个书籍的作者信息可以如下：

```python
# 先查询到某书籍的信息
book_obj = Book.objects.get(id=4)
# 在查询到作者信息
authors_obj = Author.objects.get(id=2)
# 通过authors字段进行关系绑定
book_obj.authors.add(authors_obj)

# 如果添加多个作者，则需要加上 *星号
authors_obj = Author.objects.all()
book_obj.authors.add(*authors_obj)
```



# 多对多删除数据

删除数据直接使用remove方法即可，例如：

```python
book_obj = Book.objects.get(id=4)
authors_obj = Author.objects.get(id=2)
book_obj.authors.remove(authors_obj)

# 如果是删除多个，则需要加上 *星号
authors_obj = Author.objects.all()
book_obj.authors.remove(*authors_obj)
```



也可以使用指定ID的方式来删除，例如：

```python
# 取消book id为2，author id为1的对应关系
book_obj = Book.objects.get(id=2)
book_obj.authors.remove(1)
```



# 多对多查询

多对多查询和一对多查询一样，可以使用双下划线进行外键查询，例如：

```python
# 查询所有pete写的书，并显示书名和价格以及作者名称
Book.objects.filter(authors__name='pete').values('name', 'price', 'authors__name')
```

> 其中authors是Book表中多对多字段



# 聚合函数

django的聚合函数可以用来进行最大值，均值等操作，首先需要引入一些函数：

```python
from django.db.models import Avg, Min, Sum, Max, Count
```



**聚合函数为aggregate**

例如求Book表中所有书的均价和总价：

```python
Book.objects.all().aggregate(Avg("price"))
Book.objects.all().aggregate(Sum("price"))
```



如果是需要多表关联，使用前面的方法过滤即可：

```python
# 求pete出版的书的总价
Book.objects.filter(authors__name='pete').aggregate(Sum("price"))
```



上边这样子写，结果的格式是一个字典，例如：

```python
{'price__sum': 1341}
{'price__sum': 99}
```

> 其中的key为条件和方法的组合



如果想自定义key，则可以这样做：

```python
# 自定义key为“pete_money”
Book.objects.filter(authors__name='pete').aggregate(pete_money=Sum('price'))
# 返回结果
{'pete_money': 99}
```



获取pete出版的书的个数：

```python
Book.objects.filter(authors__name='pete').aggregate(Count('name'))
```

> Count中的条件是什么字段都可以，但是必须有



# 分组

**分组函数为annotate**



例如下面的需求就可以使用分组：获取每一个作者出版的书籍的价格总价：

```python
Book.objects.values("authors__name").annotate(Sum("price"))
```

> 这里先分组，使用values指定分组的字段名称，这里是作者的名称，然后使用分组方法，指定处理函数为Sum根据价格求和



其返回的结果为Queryset格式，例如：

```python
<QuerySet [{'authors__name': 'pete', 'price__sum': 154}, {'authors__name': 'alex', 'price__sum': 99},...]>
```



例如：获取每一个出版社出版的最便宜的书：

```python
Publish.objects.values("name").annotate(pub_min=Min("book__price"))
```

> 现根据出版社的name进行分组，然后调用annotate进行处理



# F查询和Q查询

前面的条件查询使用的是filter和get，这两种查询条件是与关系，如果想设置或或者非的条件查询关系，则filter和get做不到，需要使用F和Q查询。



首先引入F和Q：

```python
from django.db.models import F, Q
```



例如这个需求：每个book的价格便宜10元：

```python
Book.objects.all().update(price=F("price")-10)
```

> 首先查找到所有的书，调用update方法进行更新，F('price')可以查询到每一本书的价格



使用Q查询可以实现或关系或者非关系查询，例如：

```python
# 查询价格为89元或者名字为go的书籍
Book.objects.filter(Q(price=89)|Q(name='go'))

# 查询书名不是go的书籍
Book.objects.filter(~Q(name='go'))
```

> Q函数中是查询条件，使用管道符 | 表示或关系，使用~ 表示非



Q查询也可以可一般的查询条件组合使用：

```python
Book.objects.filter(Q(name='go'), price="20")
```

> 但是，Q查询一定要在条件第一个