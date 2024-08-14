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
                self.dataChanged.emit(index, index, [Qt.CheckStateRole])
                return True
        if role == Qt.DisplayRole:
            if index.column() == 1:
                self.items[index.row()].name = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
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

    def parent(self, index=QModelIndex()):
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

    sig_selection_changed = pyqtSignal()
    sig_double_clicked = pyqtSignal()
    sig_itemChanged = pyqtSignal(LabelItem)
    def __init__(self, parent=None):
        super(LabelTableView, self).__init__(parent)

        self.model = LabelListModel()
        self._proxyModel = LabelProxyModel()
        self._proxyModel.setSourceModel(self.model)
        self.setModel(self._proxyModel)

        self.model.dataChanged.connect(self.onDataChanged)

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
        self.setEditTriggers(QAbstractItemView.DoubleClicked)

        self.setMouseTracking(True)
        self.doubleClicked.connect(self.sltDoubleClicked)

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

    def sltDoubleClicked(self,index):
        #print("doubleClicked %d" % index.row())
        #index is selected ?

        selcted = self.selectionModel().isSelected(index)

        if selcted:
            self.sig_double_clicked.emit()

    def selectionChanged(self, selected, deselected):
        super(LabelTableView, self).selectionChanged(selected, deselected)
        ## emit sig_selection_changed
        self.sig_selection_changed.emit()


    def selectedItems(self):
        items = []
        for index in self.selectionModel().selectedRows():
            items.append(self.model.getNodeByIndex(self._proxyModel.mapToSource(index)))
        return items

    def item(self,row):
        return self.model.getNodeByIndex(self.model.index(row,0))

    def count(self):
        return self.model.rowCount()

    def selectByShape(self, shape):
        for i, item in enumerate(self.model.items):
            if item.LabelShape == shape:
                self.scrollTo(self.model.index(i, 0))
                self.selectRow(i)
                break

    def findByShape(self, shape):
        for i, item in enumerate(self.model.items):
            if item.LabelShape == shape:
                return item
        return None

    def remByShape(self, shape):
        for i, item in enumerate(self.model.items):
            if item.LabelShape == shape:
                self.model.remove(i)
                break

    def selectLast(self):
        if self.count() > 0:
            self.selectRow(self.count() - 1)

    def toggleAll(self, checked):
        for item in self.model.items:
            item.checked = checked
        self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(self.model.rowCount() - 1, 0))

    def onDataChanged(self, topLeft, bottomRight, roles):
        for i in range(topLeft.row(), bottomRight.row() + 1):
            labelItem = self.model.getNodeByIndex(self.model.index(i, 0))
            self.sig_itemChanged.emit(labelItem)


    def modifyItemName(self, item, name):
        item.name = name
        self.model.dataChanged.emit(self.model.index(self.model.items.index(item), 1), self.model.index(self.model.items.index(item), 1), [Qt.DisplayRole])
