from pyqtgraph_karl.parametertree import ParameterTree as PP

# since we went back to native style this class if not needed any more


class ParameterTree(PP):

    def __init__(self, *args, **kwargs):
        PP.__init__(self, *args, **kwargs)
        # QtStyle 'fusion'
        # make alternating colour constrast too strong
        # and selected items barely visible...
        # change that:
        self.setStyleSheet('''
                QTreeWidget {
                    background: white;
                    alternate-background-color: Aliceblue;
                            }
                QTreeWidget::item:selected {
                    background: #6ea1f1;
                                        }''')
