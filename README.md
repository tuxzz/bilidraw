# bilidraw
Bilibili夏日绘板自动绘制工具

### 概览
**bili.py: 绘制工具**
* 将EditThisCookie导出的cookie保存为扩展名为.cookie的文件放入accounts文件夹
* 修改其中的writePos变量控制绘制目标左上角的位置，格式为tuple(y, x)
* 默认载入aria_cut.png作为目标图像，图像内颜色需全部为绘板调色板颜色
* 默认载入aria_mask.png作为遮罩图像，黑色区域表示需要绘制，其他颜色区域表示无需绘制
* 可以使用**loadJsonImage(path)**函数载入一个json中的图像数据，详情见common.py#L202

**showblock.py: 显示工具**
* y, x变量为显示左上角，显示宽高默认从aria_cut.png读取

**common.py: 一些公共函数**

**bili.ACT: 适用于Photoshop的夏日绘板调色板文件**

### 特点
* 精确计时：自动计算并抵消绘制延迟，最大化绘制效率
* 最小化绘制区域：支持遮罩，绘制前执行检测，仅绘制颜色不同的像素
* 自动屏蔽不可用账号： 重试超过6次且返回值为Not login(-101)的账号将被加入黑名单(black.json)
  运行时修改黑名单文件可以被自动重新加载。
* 多账号动态加载：放入accounts中且不在黑名单中的cookie文件可在运行时动态加载

（注：本项目只是tuxzz花费一个半小时搞出来的“能用”的程序，别指望Bugfree或者有多好的错误处理）
