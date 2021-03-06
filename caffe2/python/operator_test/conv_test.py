from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from hypothesis import assume, given
import hypothesis.strategies as st
import collections

from caffe2.python import core, workspace
import caffe2.python.hypothesis_test_util as hu


class TestConvolution(hu.HypothesisTestCase):
    # CUDNN does NOT support different padding values and we skip it
    @given(stride_h=st.integers(1, 3),
           stride_w=st.integers(1, 3),
           pad_t=st.integers(0, 3),
           pad_l=st.integers(0, 3),
           pad_b=st.integers(0, 3),
           pad_r=st.integers(0, 3),
           kernel=st.integers(3, 5),
           size=st.integers(1, 8),
           input_channels=st.integers(1, 3),
           output_channels=st.integers(1, 3),
           batch_size=st.integers(1, 3),
           order=st.sampled_from(["NCHW", "NHWC"]),
           engine=st.sampled_from(["", "EIGEN"]),
           shared_buffer=st.booleans(),
           use_bias=st.booleans(),
           **hu.gcs)
    def test_convolution_separate_stride_pad_gradients(self, stride_h, stride_w,
                                                       pad_t, pad_l, pad_b,
                                                       pad_r, kernel, size,
                                                       input_channels,
                                                       output_channels,
                                                       batch_size, order,
                                                       engine, shared_buffer,
                                                       use_bias,
                                                       gc, dc):
        op = core.CreateOperator(
            "Conv",
            ["X", "w", "b"] if use_bias else ["X", "w"],
            ["Y"],
            stride_h=stride_h,
            stride_w=stride_w,
            pad_t=pad_t,
            pad_l=pad_l,
            pad_b=pad_b,
            pad_r=pad_r,
            kernel=kernel,
            order=order,
            engine=engine,
            shared_buffer=int(shared_buffer),
        )
        X = np.random.rand(
            batch_size, size, size, input_channels).astype(np.float32) - 0.5
        w = np.random.rand(
            output_channels, kernel, kernel, input_channels).astype(np.float32)\
            - 0.5
        b = np.random.rand(output_channels).astype(np.float32) - 0.5
        if order == "NCHW":
            X = X.transpose((0, 3, 1, 2))
            w = w.transpose((0, 3, 1, 2))

        inputs = [X, w, b] if use_bias else [X, w]

        # Error handling path.
        if size + pad_r + pad_l < kernel or size + pad_t + pad_b < kernel:
            with self.assertRaises(RuntimeError):
                self.assertDeviceChecks(dc, op, inputs, [0])
            return

        self.assertDeviceChecks(dc, op, inputs, [0])
        for i in range(len(inputs)):
            self.assertGradientChecks(gc, op, inputs, i, [0])

    # CUDNN does NOT support different padding values and we skip it
    @given(stride_h=st.integers(1, 3),
            stride_w=st.integers(1, 3),
            pad_t=st.integers(0, 3),
            pad_l=st.integers(0, 3),
            pad_b=st.integers(0, 3),
            pad_r=st.integers(0, 3),
            kernel=st.integers(1, 5),
            size=st.integers(7, 10),
            input_channels=st.integers(1, 8),
            output_channels=st.integers(1, 8),
            batch_size=st.integers(1, 3),
            engine=st.sampled_from(["", "EIGEN"]),
            use_bias=st.booleans(),
            **hu.gcs)
    def test_convolution_separate_stride_pad_layout(self, stride_h, stride_w,
                                                    pad_t, pad_l, pad_b, pad_r,
                                                    kernel, size,
                                                    input_channels,
                                                    output_channels, batch_size,
                                                    engine, use_bias, gc, dc):
        X = np.random.rand(
            batch_size, size, size, input_channels).astype(np.float32) - 0.5
        w = np.random.rand(
            output_channels, kernel, kernel, input_channels).astype(np.float32)\
            - 0.5
        b = np.random.rand(output_channels).astype(np.float32) - 0.5
        outputs = {}
        for order in ["NCHW", "NHWC"]:
            op = core.CreateOperator(
                "Conv",
                ["X", "w", "b"] if use_bias else ["X", "w"],
                ["Y"],
                stride_h=stride_h,
                stride_w=stride_w,
                kernel=kernel,
                pad_t=pad_t,
                pad_l=pad_l,
                pad_b=pad_b,
                pad_r=pad_r,
                order=order,
                engine=engine,
                device_option=gc,
            )
            if order == "NCHW":
                X_f = X.transpose((0, 3, 1, 2))
                w_f = w.transpose((0, 3, 1, 2))
            else:
                X_f = X
                w_f = w
            self.ws.create_blob("X").feed(X_f, device_option=gc)
            self.ws.create_blob("w").feed(w_f, device_option=gc)
            self.ws.create_blob("b").feed(b, device_option=gc)
            self.ws.run(op)
            outputs[order] = self.ws.blobs["Y"].fetch()
        np.testing.assert_allclose(
            outputs["NCHW"],
            outputs["NHWC"].transpose((0, 3, 1, 2)),
            atol=1e-4,
            rtol=1e-4)

    @given(stride=st.integers(1, 3),
           pad=st.integers(0, 3),
           kernel=st.integers(1, 5),
           dilation=st.integers(1, 3),
           size=st.integers(7, 10),
           input_channels=st.integers(1, 8),
           output_channels=st.integers(1, 8),
           batch_size=st.integers(1, 3),
           order=st.sampled_from(["NCHW", "NHWC"]),
           engine=st.sampled_from(["", "CUDNN", "MKLDNN"]),
           use_bias=st.booleans(),
           **hu.gcs)
    def test_convolution_gradients(self, stride, pad, kernel, dilation, size,
                                   input_channels, output_channels, batch_size,
                                   order, engine, use_bias, gc, dc):
        dkernel = dilation * (kernel - 1) + 1

        assume("" == engine or 1 == dilation)
        assume(engine != "MKLDNN" or use_bias is True)

        op = core.CreateOperator(
            "Conv",
            ["X", "w", "b"] if use_bias else ["X", "w"],
            ["Y"],
            stride=stride,
            kernel=kernel,
            dilation=dilation,
            pad=pad,
            order=order,
            engine=engine,
        )
        X = np.random.rand(
            batch_size, size, size, input_channels).astype(np.float32) - 0.5
        w = np.random.rand(
            output_channels, kernel, kernel, input_channels).astype(np.float32)\
            - 0.5
        b = np.random.rand(output_channels).astype(np.float32) - 0.5
        if order == "NCHW":
            X = X.transpose((0, 3, 1, 2))
            w = w.transpose((0, 3, 1, 2))

        inputs = [X, w, b] if use_bias else [X, w]
        # Error handling path.
        if size + pad + pad < dkernel or size + pad + pad < dkernel:
            with self.assertRaises(RuntimeError):
                self.assertDeviceChecks(dc, op, inputs, [0])
            return

        self.assertDeviceChecks(dc, op, inputs, [0])
        for i in range(len(inputs)):
            self.assertGradientChecks(gc, op, inputs, i, [0])

    @given(stride=st.integers(1, 3),
           pad=st.integers(0, 3),
           kernel=st.integers(1, 5),
           dilation=st.integers(1, 3),
           size=st.integers(7, 10),
           input_channels=st.integers(1, 8),
           output_channels=st.integers(1, 8),
           batch_size=st.integers(1, 3),
           use_bias=st.booleans(),
           **hu.gcs)
    def test_convolution_layout(self, stride, pad, kernel, dilation, size,
                                input_channels, output_channels, batch_size,
                                use_bias, gc, dc):
        assume(size >= dilation * (kernel - 1) + 1)

        X = np.random.rand(
            batch_size, size, size, input_channels).astype(np.float32) - 0.5
        w = np.random.rand(
            output_channels, kernel, kernel, input_channels).astype(np.float32)\
            - 0.5
        b = np.random.rand(output_channels).astype(np.float32) - 0.5
        Output = collections.namedtuple("Output", ["Y", "engine", "order"])
        outputs = []
        for order in ["NCHW", "NHWC"]:
            for engine in (["", "CUDNN"] if dilation == 1 else [""]):
                op = core.CreateOperator(
                    "Conv",
                    ["X", "w", "b"] if use_bias else ["X", "w"],
                    ["Y"],
                    stride=stride,
                    kernel=kernel,
                    dilation=dilation,
                    pad=pad,
                    order=order,
                    engine=engine,
                    device_option=gc,
                )
                if order == "NCHW":
                    X_f = X.transpose((0, 3, 1, 2))
                    w_f = w.transpose((0, 3, 1, 2))
                else:
                    X_f = X
                    w_f = w
                self.assertDeviceChecks(
                    dc,
                    op,
                    [X_f, w_f, b] if use_bias else [X_f, w_f],
                    [0])
                self.ws.create_blob("X").feed(X_f, device_option=gc)
                self.ws.create_blob("w").feed(w_f, device_option=gc)
                self.ws.create_blob("b").feed(b, device_option=gc)
                self.ws.run(op)
                outputs.append(Output(
                    Y=self.ws.blobs["Y"].fetch(), engine=engine, order=order))

        def canonical(o):
            if o.order == "NHWC":
                return o.Y.transpose((0, 3, 1, 2))
            else:
                return o.Y

        for o in outputs:
            np.testing.assert_allclose(
                canonical(outputs[0]),
                canonical(o),
                atol=1e-4,
                rtol=1e-4)

    @given(num_workers=st.integers(1, 4),
           net_type=st.sampled_from(
               ["simple", "dag"] +
               (["async_dag"] if workspace.has_gpu_support else [])),
           do=st.sampled_from(hu.device_options),
           engine=st.sampled_from(["CUDNN", ""]))
    def test_convolution_sync(self, net_type, num_workers, do, engine):
        from caffe2.python.cnn import CNNModelHelper
        m = CNNModelHelper()
        n = 1
        d = 2
        depth = 3
        iters = 5
        h = 5
        w = 5
        workspace.ResetWorkspace()

        np.random.seed(1701)
        # Build a binary tree of conv layers, summing at each node.
        for i in reversed(range(depth)):
            for j in range(2 ** i):
                bottom_1 = "{}_{}".format(i + 1, 2 * j)
                bottom_2 = "{}_{}".format(i + 1, 2 * j + 1)
                mid_1 = "{}_{}_m".format(i + 1, 2 * j)
                mid_2 = "{}_{}_m".format(i + 1, 2 * j + 1)
                top = "{}_{}".format(i, j)
                w1, b1, w2, b2 = np.random.randn(4).tolist()
                m.Conv(
                    bottom_1, mid_1,
                    dim_in=d, dim_out=d,
                    kernel=3,
                    weight_init=m.ConstantInit(w1),
                    bias_init=m.ConstantInit(b1),
                    cudnn_state=np.random.randint(0, 3),
                    stride=1,
                    pad=1,
                    deterministic=1,
                    engine=engine)
                m.Conv(
                    bottom_2, mid_2,
                    dim_in=d, dim_out=d,
                    kernel=3,
                    stride=1,
                    pad=1,
                    weight_init=m.ConstantInit(w2),
                    bias_init=m.ConstantInit(b2),
                    deterministic=1,
                    cudnn_state=np.random.randint(0, 3),
                    engine=engine)
                m.net.Sum([mid_1, mid_2], top)

        m.net.Flatten(["0_0"], ["0_0_flat"])
        m.net.SquaredL2Distance(["0_0_flat", "label"], "xent")
        m.net.AveragedLoss("xent", "loss")
        input_to_grad = m.AddGradientOperators(["loss"])
        m.Proto().device_option.CopyFrom(do)
        m.param_init_net.Proto().device_option.CopyFrom(do)
        m.Proto().type = net_type
        m.Proto().num_workers = num_workers
        self.ws.run(m.param_init_net)

        def run():
            import numpy as np
            np.random.seed(1701)
            input_blobs = ["{}_{}".format(depth, j) for j in range(2 ** depth)]
            for input_blob in input_blobs:
                self.ws.create_blob(input_blob).feed(
                    np.random.randn(n, d, h, w).astype(np.float32),
                    device_option=do)
                self.ws.create_blob("label").feed(
                    np.random.randn(n, d * h * w).astype(np.float32),
                    device_option=do)
            self.ws.run(m.net)
            gradients = [
                self.ws.blobs[str(input_to_grad[input_blob])].fetch()
                for input_blob in input_blobs]
            return gradients

        outputs = [run() for _ in range(iters)]
        for output in outputs[1:]:
            np.testing.assert_array_equal(outputs[0], output)
            np.testing.assert_allclose(
                np.sum(np.square(output)),
                1763719461732352.0,
                rtol=1e-5)


if __name__ == "__main__":
    import unittest
    unittest.main()
