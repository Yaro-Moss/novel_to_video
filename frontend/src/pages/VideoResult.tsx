import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    Button,
    Typography,
    Space,
    List,
    App,
    Spin,
    Image,
    Row,
    Col
} from 'antd';
import {
    ArrowLeftOutlined,
    DownloadOutlined,
    VideoCameraOutlined,
    AudioOutlined,
    PictureOutlined,
    PlayCircleOutlined,
    LoadingOutlined
} from '@ant-design/icons';
import { projectApi } from '../services/api';
import type { Project } from '../types/project';
import api from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;

interface Asset {
    name: string;
    size: number;
}

interface AssetsResponse {
    audio: Asset[];
    images: Asset[];
    video_segments: Asset[];
    final_video: Asset | null;
}

export default function VideoResult() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { message } = App.useApp();
    const [project, setProject] = useState<Project | null>(null);
    const [assets, setAssets] = useState<AssetsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [imageUrls, setImageUrls] = useState<Record<string, string>>({});
    const [audioUrls, setAudioUrls] = useState<Record<string, string>>({});
    const [videoSegmentUrls, setVideoSegmentUrls] = useState<Record<string, string>>({});
    const [loadingImages, setLoadingImages] = useState<Record<string, boolean>>({});
    const [loadingAudios, setLoadingAudios] = useState<Record<string, boolean>>({});
    const [loadingVideoSegments, setLoadingVideoSegments] = useState<Record<string, boolean>>({});

    const projectId = parseInt(id || '0');

    const blobUrlsRef = useRef<Set<string>>(new Set());
    const mountedRef = useRef(true);
    const cleanupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const createBlobUrl = useCallback((data: BlobPart): string => {
        const url = window.URL.createObjectURL(new Blob([data]));
        blobUrlsRef.current.add(url);
        return url;
    }, []);

    const revokeBlobUrl = useCallback((url: string) => {
        if (blobUrlsRef.current.has(url)) {
            window.URL.revokeObjectURL(url);
            blobUrlsRef.current.delete(url);
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;

        if (cleanupTimerRef.current) {
            clearTimeout(cleanupTimerRef.current);
            cleanupTimerRef.current = null;
        }

        fetchData();

        return () => {
            mountedRef.current = false;
            cleanupTimerRef.current = setTimeout(() => {
                if (!mountedRef.current) {
                    blobUrlsRef.current.forEach(url => {
                        try { window.URL.revokeObjectURL(url); } catch {}
                    });
                    blobUrlsRef.current.clear();
                }
            }, 100);
        };
    }, [id]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [projectRes, assetsRes] = await Promise.all([
                projectApi.getDetail(projectId),
                projectApi.getAssets(projectId)
            ]);
            setProject(projectRes.data);
            setAssets(assetsRes.data);
            
            loadVideo().catch(() => console.log('视频可能还未生成'));
        } catch (err) {
            message.error('获取数据失败');
        } finally {
            setLoading(false);
        }
    };

    const loadVideo = async () => {
        try {
            const response = await projectApi.getVideo(projectId);
            const url = createBlobUrl(response.data);
            setVideoUrl(prev => {
                if (prev) revokeBlobUrl(prev);
                return url;
            });
        } catch (err) {
            console.error('加载视频失败:', err);
        }
    };

    const loadImage = async (index: number) => {
        if (imageUrls[index] || loadingImages[index]) return;
        
        try {
            setLoadingImages(prev => ({ ...prev, [index]: true }));
            const response = await api.get(`/projects/${projectId}/images/${index}`, {
                responseType: 'blob'
            });
            const url = createBlobUrl(response.data);
            setImageUrls(prev => {
                if (prev[index]) revokeBlobUrl(prev[index]);
                return { ...prev, [index]: url };
            });
        } catch (err) {
            console.error('加载图片失败:', err);
            message.warning('该图片文件暂不可用');
        } finally {
            setLoadingImages(prev => ({ ...prev, [index]: false }));
        }
    };

    const loadAudio = async (index: number) => {
        if (audioUrls[index] || loadingAudios[index]) return;
        
        try {
            setLoadingAudios(prev => ({ ...prev, [index]: true }));
            const response = await api.get(`/projects/${projectId}/audio/${index}`, {
                responseType: 'blob'
            });
            const url = createBlobUrl(response.data);
            setAudioUrls(prev => {
                if (prev[index]) revokeBlobUrl(prev[index]);
                return { ...prev, [index]: url };
            });
        } catch (err) {
            console.error('加载音频失败:', err);
            message.warning('该音频文件暂不可用');
        } finally {
            setLoadingAudios(prev => ({ ...prev, [index]: false }));
        }
    };

    const loadVideoSegment = async (index: number) => {
        if (videoSegmentUrls[index] || loadingVideoSegments[index]) return;
        
        try {
            setLoadingVideoSegments(prev => ({ ...prev, [index]: true }));
            const response = await api.get(`/projects/${projectId}/video-segments/${index}`, {
                responseType: 'blob'
            });
            const url = createBlobUrl(response.data);
            setVideoSegmentUrls(prev => {
                if (prev[index]) revokeBlobUrl(prev[index]);
                return { ...prev, [index]: url };
            });
        } catch (err) {
            console.error('加载视频片段失败:', err);
            message.warning('该视频片段暂不可用');
        } finally {
            setLoadingVideoSegments(prev => ({ ...prev, [index]: false }));
        }
    };

    const getSegmentIndex = (name: string) => {
        const match = name.match(/segment_(\d+)\./);
        return match ? parseInt(match[1]) : -1;
    };

    const downloadVideo = async () => {
        try {
            const response = await projectApi.getVideoDownload(projectId);
            const url = createBlobUrl(response.data);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${project?.name || 'video'}.mp4`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => revokeBlobUrl(url), 1000);
            message.success('下载开始');
        } catch (err) {
            message.error('下载失败');
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    if (loading) {
        return (
            <Layout className="min-h-screen">
                <Content className="flex items-center justify-center">
                    <Spin size="large" />
                </Content>
            </Layout>
        );
    }

    if (!project) {
        return (
            <Layout className="min-h-screen">
                <Content className="flex flex-col items-center justify-center p-8">
                    <div className="text-center">
                        <p>项目不存在</p>
                        <Button
                            className="mt-4"
                            icon={<ArrowLeftOutlined />}
                            onClick={() => navigate('/')}
                        >
                            返回项目列表
                        </Button>
                    </div>
                </Content>
            </Layout>
        );
    }

    return (
        <Layout className="min-h-screen bg-gray-50">
            <Content className="p-6">
                <div className="max-w-5xl mx-auto">
                    <div className="flex items-center justify-between mb-6">
                        <Space>
                            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/project/${id}`)}>
                                返回项目详情
                            </Button>
                            <Title level={2} style={{ margin: 0 }}>{project.name} - 结果</Title>
                        </Space>
                    </div>

                    {/* 项目状态提示 */}
    {project && (
        <Card className="mb-6">
            <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>项目状态: {project.status}</Text>
                {project.status !== 'completed' && (
                    <Text type="warning">项目尚未完成，部分资源可能不可用</Text>
                )}
            </Space>
        </Card>
    )}

    {/* 最终视频 */}
    <Card title="最终视频" className="mb-6">
        <div className="aspect-video bg-black rounded-lg overflow-hidden mb-4">
            {videoUrl ? (
                <video
                    className="w-full h-full"
                    controls
                    src={videoUrl}
                />
            ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-white p-4 text-center">
                    <VideoCameraOutlined style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }} />
                    <Text>视频尚未生成或暂不可用</Text>
                </div>
            )}
        </div>
        {videoUrl && (
            <Button type="primary" icon={<DownloadOutlined />} onClick={downloadVideo}>
                下载视频
            </Button>
        )}
    </Card>

    {assets && (
        <>
            {/* 图片文件 */}
            {assets.images.length > 0 && (
                <Card title="图片文件" className="mb-6">
                    <Row gutter={[16, 16]}>
                        {assets.images.map((item, idx) => {
                            const segmentIndex = getSegmentIndex(item.name);
                            const imageUrl = imageUrls[segmentIndex];
                            const isLoading = loadingImages[segmentIndex];
                            return (
                                <Col xs={12} sm={8} md={6} key={idx}>
                                    <Card
                                        hoverable
                                        cover={
                                            imageUrl ? (
                                                <Image
                                                    src={imageUrl}
                                                    alt={item.name}
                                                    style={{ height: 160, objectFit: 'cover' }}
                                                />
                                            ) : (
                                                <div
                                                    style={{
                                                        height: 160,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        backgroundColor: '#f0f0f0',
                                                        cursor: 'pointer'
                                                    }}
                                                    onClick={() => !isLoading && loadImage(segmentIndex)}
                                                >
                                                    {isLoading ? (
                                                        <Spin indicator={<LoadingOutlined spin />} />
                                                    ) : (
                                                        <Space direction="vertical" size="small">
                                                            <PictureOutlined style={{ fontSize: 32, color: '#aaa' }} />
                                                            <Text type="secondary">点击加载</Text>
                                                        </Space>
                                                    )}
                                                </div>
                                            )
                                        }
                                    >
                                        <Card.Meta
                                            title={item.name}
                                            description={formatFileSize(item.size)}
                                        />
                                    </Card>
                                </Col>
                            );
                        })}
                    </Row>
                </Card>
            )}

            {/* 音频文件 */}
            {assets.audio.length > 0 && (
                <Card title="音频文件" className="mb-6">
                    <List
                        dataSource={assets.audio}
                        renderItem={(item) => {
                            const segmentIndex = getSegmentIndex(item.name);
                            const audioUrl = audioUrls[segmentIndex];
                            const isLoading = loadingAudios[segmentIndex];
                            return (
                                <List.Item
                                    actions={[
                                        !audioUrl && !isLoading && (
                                            <Button
                                                type="link"
                                                onClick={() => loadAudio(segmentIndex)}
                                                icon={<PlayCircleOutlined />}
                                            >
                                                加载
                                            </Button>
                                        )
                                    ].filter(Boolean)}
                                >
                                    <List.Item.Meta
                                        avatar={
                                            isLoading ? (
                                                <Spin indicator={<LoadingOutlined spin />} />
                                            ) : (
                                                <AudioOutlined />
                                            )
                                        }
                                        title={item.name}
                                        description={
                                            <>
                                                <Text type="secondary">{formatFileSize(item.size)}</Text>
                                                {audioUrl && (
                                                    <div style={{ marginTop: 8 }}>
                                                        <audio
                                                            controls
                                                            src={audioUrl}
                                                            style={{ width: '100%', maxWidth: 400 }}
                                                        />
                                                    </div>
                                                )}
                                            </>
                                        }
                                    />
                                </List.Item>
                            );
                        }}
                    />
                </Card>
            )}

            {/* 视频片段 */}
            {assets.video_segments.length > 0 && (
                <Card title="视频片段" className="mb-6">
                    <List
                        dataSource={assets.video_segments}
                        renderItem={(item) => {
                            const segmentIndex = getSegmentIndex(item.name);
                            const videoSegmentUrl = videoSegmentUrls[segmentIndex];
                            const isLoading = loadingVideoSegments[segmentIndex];
                            return (
                                <List.Item>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <Space>
                                            <VideoCameraOutlined />
                                            <Text strong>{item.name}</Text>
                                            <Text type="secondary">{formatFileSize(item.size)}</Text>
                                            {!videoSegmentUrl && !isLoading && (
                                                <Button
                                                    type="primary"
                                                    size="small"
                                                    icon={<PlayCircleOutlined />}
                                                    onClick={() => loadVideoSegment(segmentIndex)}
                                                >
                                                    加载并播放
                                                </Button>
                                            )}
                                            {isLoading && (
                                                <Spin indicator={<LoadingOutlined spin />} size="small" />
                                            )}
                                        </Space>
                                        {videoSegmentUrl && (
                                            <div 
                                                style={{ 
                                                    width: '100%', 
                                                    maxWidth: 400,
                                                    marginTop: 8 
                                                }}
                                            >
                                                <video
                                                    controls
                                                    src={videoSegmentUrl}
                                                    style={{ 
                                                        width: '100%',
                                                        borderRadius: 8
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </Space>
                                </List.Item>
                            );
                        }}
                    />
                </Card>
            )}
        </>
    )}
                </div>
            </Content>
        </Layout>
    );
}
