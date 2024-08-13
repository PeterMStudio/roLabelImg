from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from shape import Shape
from lib import struct


# Define a custom struct for storing data
class LabelItem:
    checked = True
    name = ''
    LabelShape = None

    def __init__(self, shape):
        super().__init__()
        self.LabelShape = shape
        self.name = shape.label


## ListModel
## columns 2 , first is checkbox, second is label name
class LabelListModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(LabelListModel, self).__init__(parent)
        ## like QList<LabelItem>
        self.items = []

    def columnCount(self, parent=...):
        return 2

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        labelItem = self.getNodeByIndex(index)
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return QVariant(labelItem.name)
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                return QVariant(Qt.Checked if labelItem.checked else Qt.Unchecked)
        return QVariant()

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                self.items[index.row()].checked = value == Qt.Checked
                return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        # column 0 is checkable
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsSelectable
        elif index.column() == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled

    def index(self, row, column, parent=...):
        return self.createIndex(row, column, self.items[row])

    def parent(self):
        return QModelIndex()

    # return LabelItem
    def getNodeByIndex(self, index):
        return self.items[index.row()]

    def clear(self):
        self.beginResetModel()
        self.items = []
        self.endResetModel()

    def load(self, items):
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def append(self, item):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.items.append(item)
        self.endInsertRows()

    def remove(self, aRow):
        self.beginRemoveRows(QModelIndex(), aRow, aRow)
        self.items.pop(aRow)
        self.endRemoveRows()


## ProxyModel
class LabelProxyModel(QSortFilterProxyModel):
    name = ''

    def __init__(self, parent=None):
        super(LabelProxyModel, self).__init__(parent)

    def setMatchName(self, name):
        self.name = name
        self.invalidateFilter()

    def clearMatchName(self):
        self.name = ''
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if self.name == '':
            return True
        sourceModel = self.sourceModel()
        data = sourceModel.getNodeByIndex(sourceModel.index(sourceRow, 1)).name
        return self.name.lower() in data.lower()

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left, Qt.DisplayRole)
        rightData = self.sourceModel().data(right, Qt.DisplayRole)
        return leftData < rightData


## ListView
class LabelTableView(QTableView):
    model = None
    _proxyModel = None

    def __init__(self, parent=None):
        super(LabelTableView, self).__init__(parent)

        self.model = LabelListModel()
        self._proxyModel = LabelProxyModel()
        self._proxyModel.setSourceModel(self.model)
        self.setModel(self._proxyModel)

        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setColumnWidth(0, 20)
        # stretch the last column
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # row height
        self.verticalHeader().setDefaultSectionSize(20)

        # trigger signal when checkbox is clicked
        self.setEditTriggers(QAbstractItemView.SelectedClicked)

        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # set background of select row
        self.setStyleSheet("QTableView::item:selected {background-color: #CCE8FF;}")

    def load(self, items):
        self.model.load(items)

    def clear(self):
        self.model.clear()

    def append(self, item):
        self.model.append(item)

    def remove(self, aRow):
        self.model.remove(aRow)

    def setMatchName(self, name):
        self._proxyModel.setMatchName(name)

    def clearMatchName(self):
        self._proxyModel.clearMatchName()

    def setSortMode(self, mode):
        ## 3种结果 正序 倒序 无序 ; 0 1 2
        print(mode)
        self.setSortingEnabled(mode != 2)
        if mode == 0:
            self._proxyModel.sort(1, Qt.AscendingOrder)
        elif mode == 1:
            self._proxyModel.sort(1, Qt.DescendingOrder)
        else:
            self._proxyModel.sort(-1)
