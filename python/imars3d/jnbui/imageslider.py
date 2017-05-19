"""
Image slider.

Can show a series of images.
User can drag the slider to go through the image series.
Hover mouse on the image shows the pixel position and value.

Problems:
- Don't know how to add unique ID to the image widget
- Probably should follow http://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Custom.html
  to refactor the widget
"""

import os, numpy as np, glob, time
import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output
from cStringIO import StringIO
import PIL


class ImageSlider:

    viewer_layout = ipyw.Layout()
    layout = ipyw.Layout()
    fmt='png'

    store = dict()

    def __init__(self, name, image_series, width, height):
        # register
        if name in self.store:
            raise RuntimeError("%s already exists" % name)
        self.name = name
        self.store[name] = self
        #
        self.width = width
        self.height = height
        self.image_series = image_series
        self.current_img = image_series[0]
        self.createPanel()
        return
    

    def createPanel(self):
        self.slider = ipyw.IntSlider(
            value=0,
            min=0,
            max=len(self.image_series)-1,
            step=1,
            description='',
            disabled=False,
            continuous_update=True,
            orientation='horizontal',
            readout=True,
            readout_format='i',
            slider_color='white',
            layout = ipyw.Layout(width="%spx" % self.width),
        )
        self.img_widget = ipyw.Image(
                value=self.getimg_bytes(),
                format=self.fmt,
                width=self.width,
                height=self.height
            )
        self.slider.observe(self.update_image, names='value')
        side = self.createSideWidget()
        self.widgets = [
            self.img_widget,
            self.slider,
        ]
        self.panel = ipyw.HBox(
            children=[
                ipyw.VBox(children=self.widgets, layout=self.viewer_layout),
                ],
            layout = self.layout
            )
        return


    def show(self):
        display(self.panel)
        display(self.createSideWidget())
        time.sleep(1)
        js = self.createJS()
        display(js)
        return

    
    def getimg_bytes(self):
        arr = self.current_img.data
        min = np.min(arr); max = np.max(arr)
        img = ((arr-min)/(max-min)*(2**15-1)).astype('int16')
        f = StringIO()
        PIL.Image.fromarray(img).save(f, self.fmt)
        return f.getvalue()


    def update_image(self, s):
        v = self.slider.value
        self.current_img = self.image_series[v]
        self.img_widget.value=self.getimg_bytes()
        return


    def get_val(self, offsetX, offsetY):
        arr = self.current_img.data
        nrows, ncols = arr.shape
        col = int(offsetX*1./self.width * ncols)
        row = int(offsetY*1./self.height * nrows)
        return arr[row, col]

    
    def createSideWidget(self):
        html = '''
        <div>X,Y:&nbsp; <span id="img_coords"></span></div>
        <div>Value:&nbsp;<span id="img_value"></span></div>
        '''
        self.side_widget = HTML(html)
        return self.side_widget


    def createJS(self):
        arr = self.current_img.data
        nrows, ncols = arr.shape
        width, height = self.width, self.height
        name = self.name
        js = '''
        <script type="text/Javascript">
        ''' + js_handle_remote_exec_output + '''
        function update_value(v) {
          $("#img_value").text(v);
        }
        var handle_kernel_call = create_ouput_handle_func(update_value);

        $("img.widget-image").mousemove(
          function(event){
            var kernel = IPython.notebook.kernel;
            var callbacks = {iopub: {'output' : handle_kernel_call}};
            var code = "imageslider.ImageSlider.store['%(name)s'].get_val("+event.offsetX+","+event.offsetY+")";
            var msg_id = kernel.execute(code, callbacks, {silent:false});
            $("#img_coords").text(Math.floor(event.offsetX*%(ncols)s/%(width)s)
                +","+Math.floor(event.offsetY*%(nrows)s/%(height)s));
          }
        );
        </script>
        ''' % locals()
        return HTML(js)
    

js_handle_remote_exec_output = """
function create_ouput_handle_func(callback) {
    return function(out){
        console.log(out.msg_type);
        console.log(out);
        var res = null;
        if (out.msg_type == "stream"){
            res = out.content.text;
        }
        // if output is a python object
        else if(out.msg_type === "execute_result"){
            res = out.content.data["text/plain"];
        }
        // if output is a python error
        else if(out.msg_type == "error"){
            res = out.content.ename + ": " + out.content.evalue;
        }
        // if output is something we haven't thought of
        else{
            res = "[out type not implemented]";  
        }
        console.log(res);
        callback(res);
    };
}
"""

