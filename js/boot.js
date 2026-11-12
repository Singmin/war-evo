// 启动保护：最先加载，故意只用最老的写法（ES5），旧安卓内核也能跑。
// 任何脚本读不进来或运行出错，都在屏幕上显示错误和浏览器内核版本，方便真机截图排查。
var bootErrors = [];
/** 在屏幕上显示一条错误（同样的内容只显示一次）；其他脚本出错时也可调用 */
function bootReport(msg, where) {
  var line = String(msg) + (where ? '  @ ' + where : '');
  for (var i = 0; i < bootErrors.length; i++) if (bootErrors[i] === line) return;
  bootErrors.push(line);
  if (bootErrors.length > 6) bootErrors.shift();
  var box = document.getElementById('bootErr');
  if (!box) {
    box = document.createElement('div');
    box.id = 'bootErr';
    box.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99;max-height:45%;overflow:auto;' +
      'padding:8px 10px;background:rgba(60,0,0,.92);color:#fff;font:12px/1.4 monospace;white-space:pre-wrap;word-break:break-all';
    box.onclick = function () { box.style.display = 'none'; };
    (document.body || document.documentElement).appendChild(box);
  }
  box.style.display = 'block';
  box.textContent = '游戏出错了（截图发给开发者，点此关闭）\n' + bootErrors.join('\n') + '\n' + navigator.userAgent;
}
window.addEventListener('error', function (e) {
  if (e && e.target && e.target !== window && (e.target.src || e.target.href)) {
    bootReport('资源加载失败', e.target.src || e.target.href);   // 脚本、样式、图片 404 等
    return;
  }
  var where = e && e.filename ? String(e.filename).replace(/^.*\//, '') + ':' + e.lineno + ':' + e.colno : '';
  bootReport(e && (e.message || e.error) || '未知错误', where);
}, true);
window.addEventListener('unhandledrejection', function (e) {
  var r = e && e.reason;
  bootReport('Promise: ' + (r && (r.message || r) || '未知原因'), '');
});
