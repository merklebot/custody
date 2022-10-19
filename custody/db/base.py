# Import all the models, so that Base has them before being
# imported by Alembic

from custody.db.base_class import Base  # noqa

from .models.storage.content import *  # noqa
from .models.storage.key import *  # noqa
from .models.user import *  # noqa
