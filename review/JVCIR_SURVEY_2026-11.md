# JVCIR 语料统计（生成文件，勿手改）

> 生成 2026-11-18T04:59:13+00:00（UTC）。来源 OpenAlex `primary_location.source.issn:1047-3203`，窗口 2025-01-10 … 2026-11-10；
> 记录 530 条，其中 `article` **514** 篇（其余为 editorial board / erratum / review）。
> 复现：`python tools/jvcir_survey.py --refresh`。

**方法及其天花板（先声明，免得被读成更强的主张）**：Elsevier 不向 Crossref/OpenAlex 交付本刊的摘要（本窗口内只有 33/514 篇拿到可解析摘要），所以**摘要词汇统计不可用**；下表所用字段只有标题、发表日期、参考文献数（`referenced_works_count`）与 OA 标志，均为元数据级事实。正文级的体例事实（图数、表数、是否有主观实验、代码链接位置）来自 `review/JVCIR_SCOPE_2026-11.md` 里 7 篇全文逐篇解剖，不在本文件里重复。

## 1 体量、参考文献、OA、命名体例

| 窗口 | 篇数 | 参考文献 中位数 (Q1–Q3) | OA 占比 | 标题为 `方法名: 说明` 的占比 |
|---|---|---|---|---|
| 2025 | 239 | 51 (43–63) | 24% | 32% |
| 2026 | 275 | 49 (38–58) | 25% | 35% |

月度节奏（篇/月）：2025-01 14，2025-02 19，2025-03 16，2025-04 18，2025-05 17，2025-06 18，2025-07 29，2025-08 15，2025-09 15，2025-10 24，2025-11 26，2025-12 28，2026-01 33，2026-02 16，2026-03 34，2026-04 24，2026-05 20，2026-06 32，2026-07 26，2026-08 27，2026-09 31，2026-10 26，2026-11 6

## 2 标题词汇（全样本，n=514）

| 术语 | 命中 | 占比 |
|---|---|---|
| diffusion / GAN / transformer | 76 | 15% |
| 3D / point cloud / mesh | 54 | 11% |
| low-light / underwater / remote sensing | 52 | 10% |
| efficient / lightweight / fast | 46 | 9% |
| multi-modal / cross-modal | 32 | 6% |
| compression / coding | 24 | 5% |
| quality assessment / perceptual | 21 | 4% |
| robust / generaliz\w* | 19 | 4% |
| survey / review / benchmark | 18 | 4% |
| Gaussian / NeRF | 10 | 2% |

## 3 主题分布（OpenAlex primary_topic）

field：Computer Science 473，Engineering 28，Medicine 5，Mathematics 2，Physics and Astronomy 2，Biochemistry, Genetics and Molecular Biology 1，Dentistry 1，Agricultural and Biological Sciences 1，Neuroscience 1

| topic | n |
|---|---|
| Image Enhancement Techniques | 55 |
| Advanced Neural Network Applications | 48 |
| Advanced Steganography and Watermarking Techniques | 31 |
| Human Pose and Action Recognition | 29 |
| Generative Adversarial Networks and Image Synthesis | 29 |
| Video Surveillance and Tracking Methods | 28 |
| 3D Shape Modeling and Analysis | 26 |
| Digital Media Forensic Detection | 19 |
| Advanced Image Processing Techniques | 18 |
| Image and Video Quality Assessment | 18 |
| Video Coding and Compression Technologies | 16 |
| Emotion and Mood Recognition | 13 |
| Multimodal Machine Learning Applications | 13 |
| Visual Attention and Saliency Detection | 13 |
| Face recognition and analysis | 12 |

## 4 与本稿同族的三支

### 4.1 3DGS / NeRF / Gaussian 线（标题+摘要命中）：11 篇，参考文献 中位数 44（29–195）

这一支全部是**训练/重建侧**的模块增量；逐篇位置见 `review/CARE_GS_GAP_2026-11-18.md` §2。

| 日期 | DOI | 标题 | refs |
|---|---|---|---|
| 2026-10-29 | `10.1016/j.jvcir.2026.105015` | Large-scale reconstruction via LiDAR–inertial–visual Gaussian Splatting | 40 |
| 2026-10-05 | `10.1016/j.jvcir.2026.104996` | Advancing 3D Gaussian Splatting in inverse rendering through flashlight augmentation | 31 |
| 2026-10-01 | `10.1016/j.jvcir.2026.104986` | GeoIn-NeRF: NeRF Inpainting with Geometry-Appearance Prior and Balanced Score Distillation | 40 |
| 2026-09-25 | `10.1016/j.jvcir.2026.104978` | Improving 3D Gaussian splatting with reliability-guided densification and hierarchical semantic supervision | 52 |
| 2026-08-22 | `10.1016/j.jvcir.2026.104943` | A 3DGS-enhanced VGGT with pseudo-ground truth for few-resource 3D reconstruction | 29 |
| 2026-04-20 | `10.1016/j.jvcir.2026.104815` | KF-GS: Kalman filter-guided Gaussian splatting for real-time high-quality dynamic scene reconstruction | 59 |
| 2026-01-19 | `10.1016/j.jvcir.2026.104727` | eGoRG: GPU-accelerated depth estimation for immersive video applications based on graph cuts | 44 |
| 2025-12-16 | `10.1016/j.jvcir.2025.104682` | Depth error points optimization for 3D Gaussian Splatting in few-shot synthesis | 50 |
| 2025-11-21 | `10.1016/j.jvcir.2025.104602` | PatchNeRF: Patch-based Neural Radiance Fields for real time view synthesis in wide-scale scenes | 39 |
| 2025-09-23 | `10.1016/j.jvcir.2025.104586` | Knowledge NeRF: Few-shot novel view synthesis for dynamic articulated objects | 48 |
| 2025-08-27 | `10.1016/j.jvcir.2025.104572` | Survey: 3D watermarking techniques | 195 |

### 4.2 压缩/编码线：8 篇，参考文献 中位数 40（24–63）

这一支全是经典点云/视频编码工程（G-PCC / V-PCC / VVC / JND 率控）；**没有一篇 3DGS 压缩**。

| 日期 | DOI | 标题 | refs |
|---|---|---|---|
| 2026-10-16 | `10.1016/j.jvcir.2026.104999` | Efficient per-pixel continuous representation and reconstruction of multi-view images | 40 |
| 2026-10-07 | `10.1016/j.jvcir.2026.104995` | Content-adaptive Scharr-based CU64 partitioning for VVC intra coding with FPGA implementation | 24 |
| 2026-08-29 | `10.1016/j.jvcir.2026.104939` | Convolution sparse coding induced prior for hyperspectral image super resolution | 63 |
| 2026-06-03 | `10.1016/j.jvcir.2026.104854` | Space-Time Correlation Adaptive-Layered Optimization for Microimage Motion Search in Plenoptic video coding | 37 |
| 2025-11-29 | `10.1016/j.jvcir.2025.104653` | Accelerating inter-frame prediction in Versatile Video Coding via deep learning-based mode selection | 40 |
| 2025-11-06 | `10.1016/j.jvcir.2025.104629` | Fast adaptive QTMT partitioning for intra 360°video coding based on gradient boosted trees | 56 |
| 2025-07-25 | `10.1016/j.jvcir.2025.104541` | Single model learned image compression utilizing multiple scaling factors | 36 |
| 2025-03-13 | `10.1016/j.jvcir.2025.104433` | Joint reference frame synthesis and post filter enhancement for Versatile Video Coding | 45 |

### 4.3 质量评估/感知线：10 篇，参考文献 中位数 49（34–84）

这一支决定审稿人对“质量保证”一词的默认期待：IQA 类工作普遍带主观实验与相关度（PLCC/SROCC）。

| 日期 | DOI | 标题 | refs |
|---|---|---|---|
| 2026-11-10 | `10.1016/j.jvcir.2026.105024` | No-reference image quality assessment based on multi-view semantic feature sensing | 52 |
| 2026-08-14 | `10.1016/j.jvcir.2026.104938` | No reference omnidirectional image quality assessment based on viewport and latitude-aware distortion adaptive correction | 83 |
| 2026-06-15 | `10.1016/j.jvcir.2026.104867` | Trans-SURNet: A linear transformer approach to model picture-wise JND distribution for SUR curve prediction | 47 |
| 2026-06-13 | `10.1016/j.jvcir.2026.104868` | QaMatch: Adaptive semi-supervised learning for no-reference image quality assessment | 38 |
| 2026-04-27 | `10.1016/j.jvcir.2026.104801` | Predicting image quality score distribution using deep neural networks | 34 |
| 2025-11-19 | `10.1016/j.jvcir.2025.104641` | Enhancing aesthetic image generation with reinforcement learning guided prompt optimization in stable diffusion | 39 |
| 2025-10-15 | `10.1016/j.jvcir.2025.104604` | MSFIQA: A multi-scale feature fusion network based on human visual perception for no-reference image quality assessment | 62 |
| 2025-08-26 | `10.1016/j.jvcir.2025.104571` | Taylor expansion-based Kolmogorov–Arnold network for blind image quality assessment | 42 |
| 2025-07-17 | `10.1016/j.jvcir.2025.104526` | Advancements in medical image quality assessment for spinal CT and MRI images | 84 |
| 2025-06-16 | `10.1016/j.jvcir.2025.104519` | Self-supervised panoramic stitched image quality assessment based on contrastive learning | 53 |

## 5 最近 30 篇（本窗口最新，用于看“现在在发什么”）

| 日期 | DOI | 标题 | refs |
|---|---|---|---|
| 2026-11-10 | `10.1016/j.jvcir.2026.105024` | No-reference image quality assessment based on multi-view semantic feature sensing | 52 |
| 2026-11-07 | `10.1016/j.jvcir.2026.105023` | STF-NeRV: A Spatial–Temporal-Frequency alignment framework for implicit neural video representation | 49 |
| 2026-11-04 | `10.1016/j.jvcir.2026.105014` | StyleGAN encoders and skin color matching GAN for face anonymization | 63 |
| 2026-11-03 | `10.1016/j.jvcir.2026.105003` | Interactive next-frame prediction with pure transformers: Learning physical dynamics in visual environments | 12 |
| 2026-11-01 | `10.1016/j.jvcir.2026.105020` | RCSCAC-Net: a robust image tampering localization network for Gaussian-blurred forgery images | 53 |
| 2026-11-01 | `10.1016/j.jvcir.2026.105022` | Beyond image stitching: A novel formulation of image stitching based on geometric and photometric consistency | 65 |
| 2026-10-30 | `10.1016/j.jvcir.2026.105021` | MDD-CR: End-to-end multimodal deepfake detection fusing spatio-temporal and spectrographic features | 88 |
| 2026-10-29 | `10.1016/j.jvcir.2026.105013` | Decoupling risk detection and captioning via dual-branch multi-scale spatial-temporal fusion for autonomous driving | 54 |
| 2026-10-29 | `10.1016/j.jvcir.2026.105015` | Large-scale reconstruction via LiDAR–inertial–visual Gaussian Splatting | 40 |
| 2026-10-29 | `10.1016/j.jvcir.2026.105012` | Semantic-invariant steganalysis for generative steganography via trace disentanglement and prototype-guided meta-learning | 36 |
| 2026-10-22 | `10.1016/j.jvcir.2026.105002` | Understanding and overcoming the breakdown of direct video embedding through pretrained representations | 51 |
| 2026-10-22 | `10.1016/j.jvcir.2026.105001` | Meta open set filtering for open set recognition | 45 |
| 2026-10-17 | `10.1016/j.jvcir.2026.105004` | Recent innovation in vision-based human activity recognition: a systematic survey | 319 |
| 2026-10-16 | `10.1016/j.jvcir.2026.104999` | Efficient per-pixel continuous representation and reconstruction of multi-view images | 40 |
| 2026-10-12 | `10.1016/j.jvcir.2026.104979` | DanceLongCam: High-speed stable long-sequence 3D dance camera movement synthesis | 33 |
| 2026-10-12 | `10.1016/j.jvcir.2026.104994` | DegFake: Fine-grained attribution of multimodal fake news under image degradation | 33 |
| 2026-10-11 | `10.1016/j.jvcir.2026.104998` | A Draft–Verifier speculative sampling framework for accelerating diffusion-based super-resolution | 34 |
| 2026-10-10 | `10.1016/j.jvcir.2026.105000` | LDFSR: a lightweight diffusion model with dynamic feature fusion for image super-resolution | 56 |
| 2026-10-08 | `10.1016/j.jvcir.2026.104987` | Adversarial Domain Adaptation and Self-Supervised Refinement for Event Sensory Data | 74 |
| 2026-10-08 | `10.1016/j.jvcir.2026.104997` | FSR-Net: Detail-preserving remote sensing image segmentation via frequency decoupling and semantic guidance | 46 |
| 2026-10-07 | `10.1016/j.jvcir.2026.104995` | Content-adaptive Scharr-based CU64 partitioning for VVC intra coding with FPGA implementation | 24 |
| 2026-10-06 | `10.1016/j.jvcir.2026.104984` | Remote sensing image dehazing network via multi-level sensing and dynamic routing | 60 |
| 2026-10-06 | `10.1016/j.jvcir.2026.104992` | Quality-aware low-light image enhancement | 60 |
| 2026-10-05 | `10.1016/j.jvcir.2026.104990` | Global-information-guided big five personality prediction model | 45 |
| 2026-10-05 | `10.1016/j.jvcir.2026.104991` | ODS-Net: An orthogonal dual-domain synergistic network for motion deblurring of underground conveyor belts | 35 |
| 2026-10-05 | `10.1016/j.jvcir.2026.104993` | MSFD-Stega: High-fidelity, high-efficiency multi-scale frequency image steganography via Stable Diffusion | 55 |
| 2026-10-05 | `10.1016/j.jvcir.2026.104996` | Advancing 3D Gaussian Splatting in inverse rendering through flashlight augmentation | 31 |
| 2026-10-03 | `10.1016/j.jvcir.2026.104988` | DAR-Net: Resolving visual and semantic ambiguity for open-vocabulary camouflaged object segmentation | 62 |
| 2026-10-03 | `10.1016/j.jvcir.2026.104989` | Multi-grained global–regional aggregation for visual place recognition | 62 |
| 2026-10-02 | `10.1016/j.jvcir.2026.104985` | FSG-Diff: Fractional spatial–frequency and expanded-context diffusion for image super-resolution | 32 |

