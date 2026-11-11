/* Contributed UI is plain DOM code running inside the page. */
(function(){
  if (!window.PyClaw) return;
  window.PyClaw.addSettingsPanel("Vision", function(){
    const cfg = window.PyClaw.state || {};
    return '<div class="sub">图片会作为像素送给支持视觉的模型；超过 VISION_MAX_BYTES 的图片退回成路径。</div>';
  });
  window.PyClaw.on("state", function(data){
    const loaded = (data.data.plugins || []).some(function(p){ return p.name === "vision" && p.enabled; });
    document.documentElement.setAttribute("data-vision", loaded ? "on" : "off");
  });
})();
