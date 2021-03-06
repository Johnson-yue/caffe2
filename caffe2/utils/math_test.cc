#include "caffe2/core/blob.h"
#include "caffe2/core/tensor.h"
#include "caffe2/utils/math.h"
#include "caffe2/core/context.h"
#include "caffe2/proto/caffe2.pb.h"
#include "gtest/gtest.h"

namespace caffe2 {

TEST(MathTest, GemmNoTransNoTrans) {
  DeviceOption option;
  CPUContext cpu_context(option);
  TensorCPU X(std::vector<int>{5, 10});
  TensorCPU W(std::vector<int>{10, 6});
  TensorCPU Y(std::vector<int>{5, 6});
  EXPECT_EQ(X.size(), 50);
  EXPECT_EQ(W.size(), 60);
  math::Set<float, CPUContext>(X.size(), 1, X.mutable_data<float>(), &cpu_context);
  math::Set<float, CPUContext>(W.size(), 1, W.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < X.size(); ++i) {
    CHECK_EQ(X.data<float>()[i], 1);
  }
  for (int i = 0; i < W.size(); ++i) {
    CHECK_EQ(W.data<float>()[i], 1);
  }

  const float kOne = 1.0;
  const float kPointFive = 0.5;
  const float kZero = 0.0;
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasNoTrans, 5, 6, 10, kOne,
                                X.data<float>(), W.data<float>(), kZero, Y.mutable_data<float>(),
                                &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 10) << i;
  }
  // Test Accumulate
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasNoTrans, 5, 6, 10, kOne,
                                X.data<float>(), W.data<float>(), kPointFive,
                                Y.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 15) << i;
  }
  // Test Accumulate
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasNoTrans, 5, 6, 10,
                                kPointFive,
                                X.data<float>(), W.data<float>(), kOne, Y.mutable_data<float>(),
                                &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 20) << i;
  }
}

TEST(MathTest, GemmNoTransTrans) {
  DeviceOption option;
  CPUContext cpu_context(option);
  TensorCPU X(std::vector<int>{5, 10});
  TensorCPU W(std::vector<int>{6, 10});
  TensorCPU Y(std::vector<int>{5, 6});
  EXPECT_EQ(X.size(), 50);
  EXPECT_EQ(W.size(), 60);
  math::Set<float, CPUContext>(X.size(), 1, X.mutable_data<float>(), &cpu_context);
  math::Set<float, CPUContext>(W.size(), 1, W.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < X.size(); ++i) {
    CHECK_EQ(X.data<float>()[i], 1);
  }
  for (int i = 0; i < W.size(); ++i) {
    CHECK_EQ(W.data<float>()[i], 1);
  }

  const float kOne = 1.0;
  const float kPointFive = 0.5;
  const float kZero = 0.0;
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasTrans, 5, 6, 10, kOne,
                                X.data<float>(), W.data<float>(), kZero, Y.mutable_data<float>(),
                                &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 10) << i;
  }
  // Test Accumulate
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasTrans, 5, 6, 10, kOne,
                                X.data<float>(), W.data<float>(), kPointFive,
                                Y.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 15) << i;
  }
  math::Gemm<float, CPUContext>(CblasNoTrans, CblasTrans, 5, 6, 10, kPointFive,
                                X.data<float>(), W.data<float>(), kOne, Y.mutable_data<float>(),
                                &cpu_context);
  EXPECT_EQ(Y.size(), 30);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 20) << i;
  }
}

TEST(MathTest, GemvNoTrans) {
  DeviceOption option;
  CPUContext cpu_context(option);
  TensorCPU A(std::vector<int>{5, 10});
  TensorCPU X(std::vector<int>{10});
  TensorCPU Y(std::vector<int>{5});
  EXPECT_EQ(A.size(), 50);
  EXPECT_EQ(X.size(), 10);
  math::Set<float, CPUContext>(A.size(), 1, A.mutable_data<float>(), &cpu_context);
  math::Set<float, CPUContext>(X.size(), 1, X.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 5);
  for (int i = 0; i < A.size(); ++i) {
    CHECK_EQ(A.data<float>()[i], 1);
  }
  for (int i = 0; i < X.size(); ++i) {
    CHECK_EQ(X.data<float>()[i], 1);
  }

  const float kOne = 1.0;
  const float kPointFive = 0.5;
  const float kZero = 0.0;
  math::Gemv<float, CPUContext>(CblasNoTrans, 5, 10, kOne, A.data<float>(), X.data<float>(),
                                kZero, Y.mutable_data<float>(), &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 10) << i;
  }
  // Test Accumulate
  math::Gemv<float, CPUContext>(CblasNoTrans, 5, 10, kOne, A.data<float>(), X.data<float>(),
                                kPointFive, Y.mutable_data<float>(), &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 15) << i;
  }
  // Test Accumulate
  math::Gemv<float, CPUContext>(CblasNoTrans, 5, 10, kPointFive, A.data<float>(),
                                X.data<float>(), kOne, Y.mutable_data<float>(),
                                &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 20) << i;
  }
}

TEST(MathTest, GemvTrans) {
  DeviceOption option;
  CPUContext cpu_context(option);
  TensorCPU A(std::vector<int>{6, 10});
  TensorCPU X(std::vector<int>{6});
  TensorCPU Y(std::vector<int>{10});
  EXPECT_EQ(A.size(), 60);
  EXPECT_EQ(X.size(), 6);
  math::Set<float, CPUContext>(A.size(), 1, A.mutable_data<float>(), &cpu_context);
  math::Set<float, CPUContext>(X.size(), 1, X.mutable_data<float>(), &cpu_context);
  EXPECT_EQ(Y.size(), 10);
  for (int i = 0; i < A.size(); ++i) {
    CHECK_EQ(A.data<float>()[i], 1);
  }
  for (int i = 0; i < X.size(); ++i) {
    CHECK_EQ(X.data<float>()[i], 1);
  }

  const float kOne = 1.0;
  const float kPointFive = 0.5;
  const float kZero = 0.0;
  math::Gemv<float, CPUContext>(CblasTrans, 6, 10, kOne, A.data<float>(), X.data<float>(),
                                kZero, Y.mutable_data<float>(), &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 6) << i;
  }
  // Test Accumulate
  math::Gemv<float, CPUContext>(CblasTrans, 6, 10, kOne, A.data<float>(), X.data<float>(),
                                kPointFive, Y.mutable_data<float>(), &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 9) << i;
  }
  // Test Accumulate
  math::Gemv<float, CPUContext>(CblasTrans, 6, 10, kPointFive, A.data<float>(),
                                X.data<float>(), kOne, Y.mutable_data<float>(),
                                &cpu_context);
  for (int i = 0; i < Y.size(); ++i) {
    CHECK_EQ(Y.data<float>()[i], 12) << i;
  }
}

}  // namespace caffe2


