""" Implementation following TF doc """

import tensorflow as tf

import utils_mnist


class BaseModel(object):
    def __init__(self):
        pass

    def model_function(self, features, labels, mode):
        pass

    def train_and_evaluate(self, data,
                           batch_size=100,
                           num_epochs=None,
                           steps=None):
        pass


class BasicModel(BaseModel):
    def __init__(self):
        super(BasicModel, self).__init__()

    def model_function(self, features, labels, mode):
        """ Model function """
        # N samples of D values and H neurons per hidden layer
        D = 32 * 32  # sample size
        C = 10  # classes
        H = 256  # units in hidden layers

        # Input layer
        input_layer = tf.reshape(features['x'], [-1, D])

        # Dense layers
        init = tf.contrib.layers.xavier_initializer()
        hidden = tf.layers.dense(inputs=input_layer,
                                 units=H,
                                 activation=tf.nn.relu,
                                 kernel_initializer=init)

        hidden2 = tf.layers.dense(inputs=hidden,
                                  units=H,
                                  activation=tf.nn.relu,
                                  kernel_initializer=init)

        # Logits Layer
        logits = tf.layers.dense(inputs=hidden2,
                                 units=C)

        predictions = {
            'classes': tf.argmax(input=logits, axis=1, name='classes'),
            'probabilities': tf.nn.softmax(logits, name='softmax_tensor')
        }

        if mode == tf.estimator.ModeKeys.PREDICT:
            return tf.estimator.EstimatorSpec(mode=mode,
                                              predictions=predictions)

        # Calculate loss
        one_hot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32),
                                    depth=C)
        loss = tf.losses.softmax_cross_entropy(onehot_labels=one_hot_labels,
                                               logits=logits)
        # loss = tf.nn.softmax_cross_entropy_with_logits_v2(labels=labels,
        #                                        logits=logits)

        # Config training
        if mode == tf.estimator.ModeKeys.TRAIN:
            optimizer = tf.train.AdamOptimizer()
            train_op = optimizer.minimize(loss=loss,
                                          global_step=tf.train.get_global_step())

            return tf.estimator.EstimatorSpec(mode=mode,
                                              loss=loss,
                                              train_op=train_op)

        # Add evaluation metrics
        eval_metric_ops = {
            'accuracy': tf.metrics.accuracy(labels=labels,
                                            predictions=predictions['classes'])
        }
        return tf.estimator.EstimatorSpec(mode=mode,
                                          loss=loss,
                                          eval_metric_ops=eval_metric_ops)

    def train_and_evaluate(self, data,
                           batch_size=100, num_epochs=None, steps=None):
        """ Trains and evaluates the model

        Args:
            data: mnist object
            batch_size: number of images to do one gradient update
            num_epochs: number of epochs to run, if `None` a number of steps are
                computed to run the equivalent to one epoch
            steps: number of steps to run,
        """
        if (num_epochs is None and steps is None) or \
            (num_epochs is not None and steps is not None):
            raise ValueError('Please set one of num_epochs or steps. '
                             'They are mutually exclusive')

        if num_epochs is None:
            steps = data.train.images.shape[0] // batch_size + 1

        tf.logging.set_verbosity(tf.logging.INFO)

        # Create estimator
        mnist_classifier = tf.estimator.Estimator(model_fn=self.model_function,
                                                  model_dir='tmp/mnist_basic_model')

        # Train the model
        if num_epochs is None:
            train_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={'x': data.train.images},
                y=data.train.labels,
                batch_size=batch_size,
                shuffle=True)

            mnist_classifier.train(input_fn=train_input_fn,
                                   steps=steps)

        else:
            train_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={'x': data.train.images},
                y=data.train.labels,
                batch_size=batch_size,
                num_epochs=num_epochs,
                shuffle=True)

            mnist_classifier.train(input_fn=train_input_fn)

        # Evaluate model
        eval_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={'x': data.test.images},
            y=data.test.labels,
            num_epochs=1,
            shuffle=False)

        return mnist_classifier.evaluate(input_fn=eval_input_fn)


if __name__ == '__main__':
    dataset = utils_mnist.load_mnist_32x32()
    model = BasicModel()

    eval_results = model.train_and_evaluate(data=dataset,
                                            batch_size=550,
                                            num_epochs=2,
                                            steps=None)
    print(eval_results)
