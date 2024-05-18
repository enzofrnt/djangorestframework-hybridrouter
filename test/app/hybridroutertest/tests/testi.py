import unittest
from unittest.mock import patch
import importlib
import sys
import unittest
from unittest.mock import patch
import importlib
import sys
from .testo import HybridRouterTestCaseWithIntermediaryViews, HybridRouterTestCaseWithoutIntermediaryViews

class TestHybridRouterWithoutSpectacular(unittest.TestCase):
    
    def setUp(self):
        super().setUp()
        modules_to_remove = [
            'hybridrouter', 'hybridrouter.hybridrouter', 'drf_spectacular', 'drf_spectacular.utils'
        ]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]

    @patch.dict('sys.modules', {'drf_spectacular': None})
    def test_import_error(self):
        import hybridrouter
        importlib.reload(hybridrouter)
        self.assertFalse(hybridrouter.DRF_SPECTACULAR)

        
class HybridRouterTestCaseWithIntermediaryViewsWithoutSpectacular(TestHybridRouterWithoutSpectacular, HybridRouterTestCaseWithIntermediaryViews):
    def setUp(cls):
        super().setUp()
    
class   HybridRouterTestCaseWithoutIntermediaryViewsWithoutSpectacular(TestHybridRouterWithoutSpectacular, HybridRouterTestCaseWithoutIntermediaryViews):
    def setUp(cls):
        super().setUp()
            