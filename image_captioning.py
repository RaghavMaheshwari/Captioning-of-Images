# -*- coding: utf-8 -*-
"""Image_Captioning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LHYQ9E9yDobUtjyovgrPTahp3tqyGoF6
"""

from google.colab import drive

drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
import glob 
from PIL import Image 
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import pickle
from tqdm import tqdm #progress bar
import pandas as pd
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import LSTM,Input, Embedding,add, Dense, Activation, Flatten,Concatenate
from keras.optimizers import Adam
from keras.models import Model
from keras.applications.inception_v3 import InceptionV3
from keras.preprocessing import image
import nltk
from keras.layers import Dropout

from keras import backend as K
K.tensorflow_backend._get_available_gpus()

!wget http://nlp.cs.illinois.edu/HockenmaierGroup/Framing_Image_Description/Flickr8k_text.zip -P /drive/My Drive/final_upload



token = 'drive/My Drive/final_upload/text/Flickr8k.token.txt'

captions = open(token, 'r').read().strip().split('\n')

d = {}
for i, row in enumerate(captions):
    row = row.split('\t')
    row[0] = row[0][:len(row[0])-2]
    if row[0] in d:
        d[row[0]].append(row[1])
    else:
        d[row[0]] = [row[1]]

d['1000268201_693b08cb0e.jpg']

images = 'drive/My Drive/final_upload/Flicker8k_Dataset/'

images

# Contains all the images
img = glob.glob(images+'*.jpg')

img[:10]

train_images_file = 'drive/My Drive/final_upload/text/Flickr_8k.trainImages.txt'

train_images = set(open(train_images_file, 'r').read().strip().split('\n'))

def split_data(l):
    temp = []
    for i in img:
        if i[len(images):] in l:
            temp.append(i)
    return temp

# Getting the training images from all the images
train_img = split_data(train_images)
len(train_img)

val_images_file = 'drive/My Drive/final_upload/text/Flickr_8k.devImages.txt'
val_images = set(open(val_images_file, 'r').read().strip().split('\n'))

# Getting the validation images from all the images
val_img = split_data(val_images)
len(val_img)

test_images_file = 'drive/My Drive/final_upload/text/Flickr_8k.testImages.txt'
test_images = set(open(test_images_file, 'r').read().strip().split('\n'))

# Getting the testing images from all the images
test_img = split_data(test_images)
print ( "total test images" + str(len(test_img)) )

Image.open(train_img[0])

def preprocess_input(x):
    x /= 255.
    x -= 0.5
    x *= 2.
    return x

def preprocess(image_path):
    img = image.load_img(image_path, target_size=(299, 299))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return x



model = InceptionV3(weights='imagenet')

from keras.models import Model # removing the softmax and last dense layer

new_input = model.input
hidden_layer = model.layers[-2].output

model_new = Model(new_input, hidden_layer)

from keras.utils import plot_model
plot_model(model_new, to_file='model1.png')

tryi = model_new.predict(preprocess(train_img[0]))

tryi.shape

tryi

def encode(image):
    image = preprocess(image)
    temp_enc = model_new.predict(image)
    temp_enc = np.reshape(temp_enc, temp_enc.shape[1])
    return temp_enc

encoding_train = {}
for img in tqdm(train_img):
    encoding_train[img[len(images):]] = encode(img)

with open("drive/My Drive/encoded_images_inceptionV3.p", "wb") as encoded_pickle:
    pickle.dump(encoding_train, encoded_pickle)

encoding_train = pickle.load(open('drive/My Drive/encoded_images_inceptionV3.p', 'rb'))



encoding_test = {}
for img in tqdm(test_img):
    encoding_test[img[len(images):]] = encode(img)

with open("drive/My Drive/encoded_images_test_inceptionV3.p", "wb") as encoded_pickle:
    pickle.dump(encoding_test, encoded_pickle)

encoding_test = pickle.load(open('drive/My Drive/encoded_images_test_inceptionV3.p', 'rb'))

encoding_test[test_img[0][len(images):]].shape

train_d = {}
for i in train_img:
    if i[len(images):] in d:
        train_d[i] = d[i[len(images):]]

train_d[images+'3556792157_d09d42bef7.jpg']

val_d = {}
for i in val_img:
    if i[len(images):] in d:
        val_d[i] = d[i[len(images):]]

len(val_d)

test_d = {}
for i in test_img:
    if i[len(images):] in d:
        test_d[i] = d[i[len(images):]]

len(test_d)

caps = []
for key, val in train_d.items():
    for i in val:
        caps.append('<start> ' + i + ' <end>')

words = [i.split() for i in caps]

unique = []
for i in words:
    unique.extend(i)

unique = list(set(unique))

with open("drive/My Drive/unique.p", "wb") as pickle_d:
     pickle.dump(unique, pickle_d)

unique = pickle.load(open('drive/My Drive/unique.p', 'rb'))

len(unique)

word2idx = {val:index for index, val in enumerate(unique)}

word2idx['<start>']

idx2word = {index:val for index, val in enumerate(unique)}

idx2word[5523]

max_len = 0
for c in caps:
    c = c.split()
    if len(c) > max_len:
        max_len = len(c)
max_len

len(unique), max_len

vocab_size = len(unique)

vocab_size

f = open('flickr8k_training_dataset.txt', 'w')
f.write("image_id\tcaptions\n")

for key, val in train_d.items():
    for i in val:
        f.write(key[len(images):] + "\t" + "<start> " + i +" <end>" + "\n")

f.close()

df = pd.read_csv('flickr8k_training_dataset.txt', delimiter='\t')

len(df)

c = [i for i in df['captions']]
len(c)

imgs = [i for i in df['image_id']]

a = c[-1]
a, imgs[-1]

for i in a.split():
    print (i, "=>", word2idx[i])

samples_per_epoch = 0
for ca in caps:
    samples_per_epoch += len(ca.split())-1

samples_per_epoch

def data_generator(batch_size = 32):
        partial_caps = []
        next_words = []
        images = []
        
        df = pd.read_csv('flickr8k_training_dataset.txt', delimiter='\t')
        df = df.sample(frac=1)
        iter = df.iterrows()
        c = []
        imgs = []
        for i in range(df.shape[0]):
            x = next(iter)
            c.append(x[1][1])
            imgs.append(x[1][0])


        count = 0
        while True:
            for j, text in enumerate(c):
                current_image = encoding_train[imgs[j]]
                for i in range(len(text.split())-1):
                    count+=1
                    
                    partial = [word2idx[txt] for txt in text.split()[:i+1]]
                    partial_caps.append(partial)
                    
                   
                    n = np.zeros(vocab_size)
                   
                    n[word2idx[text.split()[i+1]]] = 1
                    next_words.append(n)  
                    
                    images.append(current_image)

                    if count>=batch_size:
                        next_words = np.asarray(next_words)
                        images = np.asarray(images)
                        partial_caps = sequence.pad_sequences(partial_caps, maxlen=max_len, padding='post') #padding for unused spaces in words
                        yield [[images, partial_caps], next_words]
                        partial_caps = []
                        next_words = []
                        images = []
                        count = 0

embedding_size = 300

from keras.layers import Bidirectional

input1 = Input(shape=(2048,))
image1 = Dropout(0.5)(input1)
image2 = Dense(256, activation='relu')(image1)

input2 = Input(shape=(max_len,))
word1 = Embedding(vocab_size,300 , mask_zero=True)(input2)
word2 = Dropout(0.5)(word1)
word3 = Bidirectional(LSTM(128, return_sequences=False))(word2)
decoder1 = add([image2, word3])
decoder2 = Dense(256, activation='relu')(decoder1)
outputs = Dense(vocab_size, activation='softmax')(decoder2) #word score to probab

final_model = Model(inputs=[input1, input2], outputs=outputs)
final_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

"""Merging the models and creating a softmax classifier"""

from keras.utils import plot_model
plot_model(final_model, to_file='model.png')





final_model.summary()

history = final_model.fit_generator(data_generator(batch_size=128), steps_per_epoch = 1000,epochs=8)

plt.plot(history.history['acc'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.show()
# summarize history for loss
plt.plot(history.history['loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.show()

final_model.save_weights('drive/My Drive/model_weight.h5')

final_model.load_weights('drive/My Drive/model_weight.h5')

def predict_captions(image):
    start_word = ["<start>"]
    while True:
        par_caps = [word2idx[i] for i in start_word]
        par_caps = sequence.pad_sequences([par_caps], maxlen=max_len, padding='post')
        e = encoding_test[image[len(images):]]
        preds = final_model.predict([np.array([e]), np.array(par_caps)])
        word_pred = idx2word[np.argmax(preds[0])]
        start_word.append(word_pred)
        
        if word_pred == "<end>" or len(start_word) > max_len:
            break
            
    return ' '.join(start_word[1:-1])

try_image = test_img[0]
img = image.load_img(try_image)
img = image.img_to_array(img)

Image.open(try_image)

print ( predict_captions(try_image))

im = 'drive/My Drive/final_upload/Flicker8k_Dataset/3767841911_6678052eb6.jpg'
img = image.load_img(im)
img = image.img_to_array(img)

Image.open(im)

print (predict_captions(im))
Image.open(im)

im = 'drive/My Drive/final_upload/Flicker8k_Dataset/2511019188_ca71775f2d.jpg'
img = image.load_img(im)
img = image.img_to_array(img)

Image.open(im)

print (predict_captions(im))
Image.open(im)



im = 'drive/My Drive/final_upload/Flicker8k_Dataset/3767841911_6678052eb6.jpg'
img = image.load_img(im)
img = image.img_to_array(img)

Image.open(im)

print (predict_captions(im))
Image.open(im)