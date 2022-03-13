import Hydrus
import Hydrus.HydrusApi as HydrusApi

data = HydrusApi.getAllMainFileData()
print(data.keys())