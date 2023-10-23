class Node(object):
    def __init__(self, name, type='', text='',
                 calling='', uniquename='',
                 model='', order=0, mxnames = '',
                 subnets = [], defaultroute = ""):
        self.name = str(name)
        self.type = str(type)
        self.text = str(text)
        self.mxnames = str(mxnames)
        self.calling = str(calling)
        self.order = order
        self.model = model
        self.defaultroute = defaultroute
        # self.children = set()
        self.children = []
        self.subnets = subnets
        if uniquename == '':
            self.uniquename = str(name)
        else:
            self.uniquename = str(uniquename)

    #All nodes including yourself
    def get_all_nodes(self):
        yield self
        for child in self.children:
            for n in child.get_all_nodes():
                yield n

    def getiterator(self, name):
        result = []
        for node in self.get_all_nodes():
            if node.name == name:
                result.append(node)
        return result

    def find(self, name):
        for node in self.children:
            if node.name == name:
                return node

    def findall(self, name):
        result = []
        for node in self.children:
            if node.name == name:
                result.append(node)
        return result

    def getchildren(self):
        for child in self.children:
            yield child

