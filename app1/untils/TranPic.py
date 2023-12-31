
# coding: utf-8

# In[1]:
import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
from PIL import Image

class TranPic(object):
    # 假如你使用的是GPU版本可以开启这两行加速
    gpus = tf.config.experimental.list_physical_devices('GPU')
    tf.config.experimental.set_memory_growth(gpus[0], True)

    # 设置最长的一条边的长度
    max_dim = 800
    # 内容图片路径
    # content_path = 'E:/Django/mysite2/mysite2/app1/static/tmp/function/TranPic/input/content.jpg'
    content_path = None
    # 风格图片路径
    # style_path = 'E:/Django/mysite2/mysite2/app1/static/tmp/function/TranPic/input/style.jpg'
    style_path = None
    # 融合图片路径
    resultPic_path = None
    # 风格权重
    style_weight=10
    # 内容权重
    content_weight=1
    # 全变差正则权重
    total_variation_weight=1e5
    # 训练次数
    stpes = 501
    # 是否保存训练过程中产生的图片
    save_img = True

    # 用于计算content loss
    # 这里只取了一层的输出进行对比，取多层输出效果变化不大
    content_layers = None

    # 用于计算风格的卷积层
    style_layers = None

    # 计算层数
    num_content_layers = None
    num_style_layers = None

    # 获得输出风格层特征的模型
    style_extractor = None
    # 图像预处理，主要是减去颜色均值，RGB转BGR
    preprocessed_input = None
    # 风格图片传入style_extractor，提取风格层的输出
    style_outputs = None

    # 构建一个返回风格特征和内容特征的模型
    extractor = None
    # 计算得到风格图片的风格特征
    style_targets = None
    # 计算得到内容图片的内容特征
    content_targets = None

    # 初始化要训练的图片
    image = None
    # 定义优化器
    opt = None

    def __init__(self,content_path,style_path,result_path):
        self.content_path = content_path
        self.style_path = style_path
        # 融合图片路径
        self.result_path = result_path
        # 载入内容图片
        content_image = self.load_img(content_path)
        # 载入风格图片
        style_image = self.load_img(style_path)
        # 显示内容图片
        # self.imshow(content_image, 'Content Image')
        # 显示风格图片
        # self.imshow(style_image, 'Style Image')

        # 用于计算content loss
        # 这里只取了一层的输出进行对比，取多层输出效果变化不大
        self.content_layers = ['block5_conv2']

        # 用于计算风格的卷积层
        self.style_layers = ['block1_conv1',
                        'block2_conv1',
                        'block3_conv1',
                        'block4_conv1',
                        'block5_conv1']

        # 计算层数
        self.num_content_layers = len(self.content_layers)
        self.num_style_layers = len(self.style_layers)

        # 获得输出风格层特征的模型
        self.style_extractor = self.vgg_layers(self.style_layers)
        # 图像预处理，主要是减去颜色均值，RGB转BGR
        self.preprocessed_input = tf.keras.applications.vgg16.preprocess_input(style_image * 255)
        # 风格图片传入style_extractor，提取风格层的输出
        self.style_outputs = self.style_extractor(self.preprocessed_input)

        # 构建一个返回风格特征和内容特征的模型
        self.extractor = self.StyleContentModel(self.style_layers, self.content_layers)
        # 计算得到风格图片的风格特征
        self.style_targets = self.extractor(style_image)['style']
        # 计算得到内容图片的内容特征
        self.content_targets = self.extractor(content_image)['content']

        # 初始化要训练的图片
        self.image = tf.Variable(content_image)
        # 定义优化器
        self.opt = tf.optimizers.Adam(learning_rate=0.02, beta_1=0.99, epsilon=1e-1)

        # 训练steps次
        for n in range(self.stpes):
            # 训练模型
            self.train_step(self.image)
            # 每训练n次打印一次图片
            if n == self.stpes - 1:
                # self.imshow(self.image.read_value(), "Train step: {}".format(n))
                # print("迭代第{}次".format(n))
                # 保存图片
                if self.save_img == True:
                    # 去掉一个维度
                    s_image = tf.squeeze(self.image)
                    # 把array变成Image对象
                    s_image = Image.fromarray(np.uint8(s_image.numpy() * 255))
                    # 设置保存路径保存图片
                    s_image.save(self.result_path)


    # 载入图片
    def load_img(self,path_to_img):
        # 读取文件内容
        img = tf.io.read_file(path_to_img)
        # 变成3通道图片数据
        img = tf.image.decode_image(img, channels=3, dtype=tf.float32)
    #     img = tf.image.convert_image_dtype(img, tf.float32)
        # 获得图片高度和宽度，并转成float类型
        shape = tf.cast(tf.shape(img)[:-1], tf.float32)
        # 最长的边的长度
        long_dim = max(shape)
        # 图像缩放，把图片最长的边变成max_dim
        scale = self.max_dim / long_dim
        new_shape = tf.cast(shape * scale, tf.int32)
        # resize图片大小
        img = tf.image.resize(img, new_shape)
        # 增加1个维度，变成4维数据
        img = img[tf.newaxis, :]
        return img

    # 用于显示图片
    def imshow(self,image, title=None):
        # 如图是4维度数据
        if len(image.shape) > 3:
            # 去掉size为1的维度如(1,300,300,3)->(300,300,3)
            image = tf.squeeze(image)
        # 显示图片
        plt.imshow(image)
        if title:
            # 设置图片title
            plt.title(title)
        plt.axis('off')
        plt.show()


    # 创建一个新模型，输入与vgg16一样，输出为指定层的输出
    def vgg_layers(self,layer_names):
        # 载入VGG16的卷积层部分
        vgg = tf.keras.applications.VGG16(include_top=False, weights='imagenet')
        # VGG16的模型参数不参与训练
        vgg.trainable = False
        # 获取指定层的输出值
        outputs = [vgg.get_layer(name).output for name in layer_names]
        # 定义一个新的模型，输入与vgg16一样，输出为指定层的输出
        model = tf.keras.Model([vgg.input], outputs)
        # 返回模型
        return model


    # Gram矩阵的计算
    def gram_matrix(self,input_tensor):
        # 爱因斯坦求和，bijc表示input_tensor中的4个维度，bijd表示input_tensor中的4个维度
        # 例如input_tensor的shape为(1,300,200,32)，那么b=1,i=300,j=200,c=32,d=32
        # ->bcd表示计算后得到的数据维度为(1,32,32),得到的结果表示特征图与特征图之间的相关性
        result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
        # 特征图的shape
        input_shape = tf.shape(input_tensor)
        # 特征图的高度乘以宽度得到特征值数量
        num_locations = tf.cast(input_shape[1]*input_shape[2], tf.float32)
        # 除以特征值的数量
        return result/(num_locations)



    # 构建一个返回风格特征和内容特征的模型
    class StyleContentModel(tf.keras.models.Model):
        vgg = None
        style_layers =None
        content_layers = None
        num_style_layers = None
        def __init__(self, style_layers, content_layers):
            super().__init__()
            # 获得输出风格层和内容层特征的模型
            self.vgg =  self.vgg_layers(style_layers + content_layers)
            # 用于计算风格的卷积层
            self.style_layers = style_layers
            # 用于计算content loss的卷积层
            self.content_layers = content_layers
            # 风格层的数量
            self.num_style_layers = len(style_layers)

        # 创建一个新模型，输入与vgg16一样，输出为指定层的输出
        def vgg_layers(self, layer_names):
            # 载入VGG16的卷积层部分
            vgg = tf.keras.applications.VGG16(include_top=False, weights='imagenet')
            # VGG16的模型参数不参与训练
            vgg.trainable = False
            # 获取指定层的输出值
            outputs = [vgg.get_layer(name).output for name in layer_names]
            # 定义一个新的模型，输入与vgg16一样，输出为指定层的输出
            model = tf.keras.Model([vgg.input], outputs)
            # 返回模型
            return model

        def gram_matrix(self, input_tensor):
            # 爱因斯坦求和，bijc表示input_tensor中的4个维度，bijd表示input_tensor中的4个维度
            # 例如input_tensor的shape为(1,300,200,32)，那么b=1,i=300,j=200,c=32,d=32
            # ->bcd表示计算后得到的数据维度为(1,32,32),得到的结果表示特征图与特征图之间的相关性
            result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
            # 特征图的shape
            input_shape = tf.shape(input_tensor)
            # 特征图的高度乘以宽度得到特征值数量
            num_locations = tf.cast(input_shape[1] * input_shape[2], tf.float32)
            # 除以特征值的数量
            return result / (num_locations)

        def call(self, inputs):
            # 图像预处理，主要是减去颜色均值，RGB转BGR
            preprocessed_input = tf.keras.applications.vgg16.preprocess_input(inputs*255.0)
            # 图片传入模型，提取风格层和内容层的输出
            outputs = self.vgg(preprocessed_input)
            # 获得风格特征输出和内容特征输出
            style_outputs, content_outputs = (outputs[:self.num_style_layers],
                                              outputs[self.num_style_layers:])
            # 计算风格特征的Gram矩阵
            style_outputs = [self.gram_matrix(style_output) for style_output in style_outputs]
            # 把风格特征的Gram矩阵分别存入字典
            style_dict = {style_name:value for style_name, value in zip(self.style_layers, style_outputs)}
            # 把内容特征存入字典
            content_dict = {content_name:value for content_name, value in zip(self.content_layers, content_outputs)}
            # 返回结果
            return {'content':content_dict, 'style':style_dict}

    # 把数值范围限制在0-1之间
    def clip_0_1(self,image):
        return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)

    # 定义风格和内容loss
    def style_content_loss(self,outputs):
        # 模型输出的风格特征
        style_outputs = outputs['style']
        # 模型输出的内容特征
        content_outputs = outputs['content']
        # 计算风格loss
        style_loss = tf.add_n([tf.reduce_mean((style_outputs[name]-self.style_targets[name])**2)
                               for name in style_outputs.keys()])
        style_loss *= self.style_weight / self.num_style_layers
        # 计算内容loss
        content_loss = tf.add_n([tf.reduce_mean((content_outputs[name]-self.content_targets[name])**2)
                                 for name in content_outputs.keys()])
        content_loss *= self.content_weight / self.num_content_layers
        # 风格加内容loss
        loss = style_loss + content_loss
        return loss

    # 施加全变差正则，全变差正则化常用于图片去噪，可以使生成的图片更加平滑自然
    def total_variation_loss(self,image):
        x_deltas = image[:,:,1:,:] - image[:,:,:-1,:]
        y_deltas = image[:,1:,:,:] - image[:,:-1,:,:]
        return tf.reduce_mean(x_deltas**2) + tf.reduce_mean(y_deltas**2)


    # 我们可以用@tf.function装饰器来将python代码转成tensorflow的图表示代码，用于加速代码运行速度
    @tf.function()
    # 定义一个训练模型的函数
    def train_step(self,image):
        # 固定写法，使用tf.GradientTape()来计算梯度
        with tf.GradientTape() as tape:
            # 传入图片获得风格特征和内容特征
            outputs = self.extractor(image)
            # 计算风格和内容loss
            loss = self.style_content_loss(outputs)
            # 再加上全变差正则loss
            loss += self.total_variation_weight*self.total_variation_loss(image)
        # 传入loss和模型参数，计算权值调整
        grad = tape.gradient(loss, image)
        # 进行权值调整，这里要调整的权值就是image图像的像素值
        self.opt.apply_gradients([(grad, image)])
        # 把数值范围限制在0-1之间
        image.assign(self.clip_0_1(image))

