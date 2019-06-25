# -*- coding: utf-8 -*-
import pydot
from graphviz import Digraph
import json
import sys

class build_crushmap_graphviz():
    """
    1. 使用命令ceph report --format=json > crush.json导出数据文件
    2. 每种类型bucket一个颜色,不够自己去color_list里面添加,支持最多10级结构
    3. 生成的文件默认问png格式,文件保存在当前目录的crushmap.png
    """
    def __init__(self):
        self.graph = pydot.Dot('ceph_crushmap', graph_type='digraph')
        self.dot = Digraph(comment='CrushMap', node_attr={'shape': 'record', 'height': '.1'})
        self.dot.graph_attr['size'] = '4096,2160'
        self.dot.graph_attr['resolution'] = '100'
        self.dot.graph_attr['bb'] = '0,0,4,8'
        self.dot.format = 'png'
        self.color_list = ["maroon", "pink", "khaki", "orange", "purple", "yellow", "cyan", "beige", "red"]
        self.save_name = "crushmap"

    def build(self, crushmap_file):
        try:
            with open(crushmap_file) as data_file:
                data = json.load(data_file)
            for i in range(len(data['crushmap']['devices'])):
                self.dot.node(str(data['crushmap']['devices'][i]['id']),
                              'device: ' + data['crushmap']['devices'][i]['name'],
                              {'style': 'filled', 'fillcolor': 'green'})
            tmp_list = []
            color_dict = {}
            for i in range(len(data['crushmap']['buckets'])):
                if data['crushmap']['buckets'][i]['type_name'] in tmp_list:
                    color_ = color_dict[data['crushmap']['buckets'][i]['type_name']]
                else:
                    tmp_list.append(data['crushmap']['buckets'][i]['type_name'])
                    color_ = self.color_list.pop()
                    color_dict[data['crushmap']['buckets'][i]['type_name']] = color_
                self.dot.node(str(data['crushmap']['buckets'][i]['id']),
                              data['crushmap']['buckets'][i]['type_name'] + ': ' + data['crushmap']['buckets'][i]['name'],
                              {'style': 'filled', 'fillcolor': color_})
            edges_list = []
            for i in range(len(data['crushmap']['buckets'])):
                for j in range(len(data['crushmap']['buckets'][i]['items'])):
                    self.dot.edge(str(data['crushmap']['buckets'][i]['id']),
                                  str(data['crushmap']['buckets'][i]['items'][j]['id']))
                    edges_list.append(
                        str(data['crushmap']['buckets'][i]['id']) + str(data['crushmap']['buckets'][i]['items'][j]['id']))
            self.dot.render(self.save_name)
            print "Sucessful, File = {}.{}".format(self.save_name,self.dot.format)
        except:
            print "Faild!"

if __name__ == '__main__':
    file_path = sys.argv[1]
    crush_make = build_crushmap_graphviz()
    crush_make.build(file_path)