import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Typography,
  Tag,
  Button,
  Input,
  Space,
  Pagination,
  Spin,
  Empty,
  App,
  Select,
  Dropdown,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
  UnorderedListOutlined,
  SoundOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  PlayCircleOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Project } from '../types/project';
import { projectApi } from '../services/api';

const { Title, Text } = Typography;

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待处理' },
  processing: { color: 'processing', text: '处理中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>();

  const fetchProjects = async (currentPage = 1, search = '', status?: string) => {
    setLoading(true);
    try {
      const response = await projectApi.getProjects({
        page: currentPage,
        page_size: pageSize,
        search: search || undefined,
        status,
      });
      setProjects(response.data.items);
      setTotal(response.data.total);
      setPage(currentPage);
    } catch (error) {
      message.error('获取项目列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleSearch = () => {
    fetchProjects(1, searchText, statusFilter);
  };

  const handlePageChange = (newPage: number, newPageSize?: number) => {
    if (newPageSize && newPageSize !== pageSize) {
      setPageSize(newPageSize);
      fetchProjects(1, searchText, statusFilter);
    } else {
      fetchProjects(newPage, searchText, statusFilter);
    }
  };

  const handleDelete = (project: Project) => {
    modal.confirm({
      title: '确认删除',
      content: `确定要删除项目"${project.name}"吗？此操作无法撤销。`,
      okText: '确认删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await projectApi.deleteProject(project.id);
          message.success('项目已删除');
          fetchProjects(page, searchText, statusFilter);
        } catch (error) {
          message.error('删除项目失败');
          console.error(error);
        }
      },
    });
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>我的项目</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/projects/create')}
        >
          新建项目
        </Button>
      </div>

      <Card style={{ marginBottom: '24px' }}>
        <Space wrap>
          <Input
            placeholder="搜索项目名称"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 150 }}
            value={statusFilter}
            onChange={(value) => {
              setStatusFilter(value);
              fetchProjects(1, searchText, value);
            }}
            options={[
              { value: 'pending', label: '待处理' },
              { value: 'processing', label: '处理中' },
              { value: 'completed', label: '已完成' },
              { value: 'failed', label: '失败' },
            ]}
          />
          <Button onClick={handleSearch}>搜索</Button>
        </Space>
      </Card>

      <Spin spinning={loading}>
        {projects.length > 0 ? (
          <>
            <List
              grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4, xxl: 4 }}
              dataSource={projects}
              renderItem={(project) => {
                const statusInfo = statusMap[project.status] || statusMap.pending;
                return (
                  <List.Item>
                    <Card
                      hoverable
                      onClick={() => navigate(`/project/${project.id}`)}
                      style={{ cursor: 'pointer' }}
                      cover={
                        <div style={{
                          height: '140px',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: project.status === 'pending' ? '#e6f7ff' : 
                                     project.status === 'processing' ? '#fff7e6' :
                                     project.status === 'completed' ? '#f6ffed' : '#fff1f0',
                        }}>
                          <FileTextOutlined style={{ 
                            fontSize: '56px', 
                            color: project.status === 'pending' ? '#1890ff' : 
                                   project.status === 'processing' ? '#fa8c16' :
                                   project.status === 'completed' ? '#52c41a' : '#ff4d4f'
                          }} />
                          <div style={{ marginTop: '12px' }}>
                            <Tag color={statusInfo.color} style={{ fontSize: '14px', padding: '4px 12px' }}>
                              {statusInfo.text}
                            </Tag>
                          </div>
                        </div>
                      }
                      actions={[
                        <Button
                          type={project.status === 'pending' ? 'primary' : 'default'}
                          icon={<PlayCircleOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/project/${project.id}`);
                          }}
                          size="small"
                        >
                          {project.status === 'pending' ? '开始生成' : '查看详情'}
                        </Button>,
                        <Dropdown
                          menu={{
                            items: [
                              {
                                key: 'segments',
                                icon: <UnorderedListOutlined />,
                                label: '分段预览',
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  navigate(`/projects/${project.id}/segments`);
                                }
                              },
                              {
                                key: 'tts',
                                icon: <SoundOutlined />,
                                label: 'TTS配置',
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  navigate(`/projects/${project.id}/tts`);
                                }
                              },
                              {
                                key: 'image',
                                icon: <PictureOutlined />,
                                label: '图像配置',
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  navigate(`/projects/${project.id}/image`);
                                }
                              },
                              {
                                key: 'video',
                                icon: <VideoCameraOutlined />,
                                label: '视频配置',
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  navigate(`/projects/${project.id}/video`);
                                }
                              },
                              { type: 'divider' },
                              {
                                key: 'delete',
                                icon: <DeleteOutlined />,
                                label: '删除项目',
                                danger: true,
                                onClick: (e) => {
                                  e.domEvent.stopPropagation();
                                  handleDelete(project);
                                }
                              }
                            ]
                          }}
                        >
                          <Button type="link" size="small" icon={<MoreOutlined />} onClick={(e) => e.stopPropagation()}>
                            更多
                          </Button>
                        </Dropdown>
                      ]}
                    >
                      <Card.Meta
                        title={
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text ellipsis style={{ maxWidth: '200px', fontSize: '16px', fontWeight: 500 }}>
                              {project.name}
                            </Text>
                          </div>
                        }
                        description={
                          <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              创建时间：{new Date(project.created_at).toLocaleString('zh-CN')}
                            </Text>
                            {project.status === 'pending' && (
                              <Text type="secondary" style={{ fontSize: '12px', color: '#1890ff' }}>
                                点击卡片或"开始生成"按钮开始处理
                              </Text>
                            )}
                          </Space>
                        }
                      />
                    </Card>
                  </List.Item>
                );
              }}
            />

            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                showSizeChanger
                showQuickJumper
                showTotal={(total) => `共 ${total} 个项目`}
                onChange={handlePageChange}
              />
            </div>
          </>
        ) : (
          <Empty
            description="暂无项目"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/projects/create')}
            >
              创建第一个项目
            </Button>
          </Empty>
        )}
      </Spin>
    </div>
  );
};

export default ProjectList;
