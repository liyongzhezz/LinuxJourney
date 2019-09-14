\* [数据表之间的关系](#数据表之间的关系)

\* [数据表结构](#数据表结构)

\* [修改数据](#修改数据)

\* [删除数据](#删除数据)

\* [单表查找数据](#单表查找数据)



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



