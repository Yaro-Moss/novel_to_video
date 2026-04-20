import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Upload,
  Button,
  App,
  Space,
} from 'antd';
import {
  UploadOutlined,
  ArrowLeftOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { UploadFile, UploadProps } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { projectApi } from '../services/api';

const { Dragger } = Upload;

const ProjectCreate: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const { message } = App.useApp();

  const props: UploadProps = {
        name: 'file',
        multiple: false,
        fileList,
        maxCount: 1,
        accept: '.txt,.pdf,.docx',
        beforeUpload: (file) => {
            const fileName = file.name.toLowerCase();
            const isValid = fileName.endsWith('.txt') || fileName.endsWith('.pdf') || fileName.endsWith('.docx');
            if (!isValid) {
                message.error('只能上传 TXT、PDF 或 DOCX 文件！');
                return Upload.LIST_IGNORE;
            }
            const isLt10M = file.size / 1024 / 1024 < 10;
            if (!isLt10M) {
                message.error('文件大小不能超过 10MB！');
                return Upload.LIST_IGNORE;
            }
            // 确保保存的文件对象包含 originFileObj
            const uploadFile: UploadFile = {
                uid: file.uid,
                name: file.name,
                status: 'done',
                originFileObj: file,
            };
            setFileList([uploadFile]);
            return false; // 阻止自动上传
        },
        onChange: (info) => {
            setFileList(info.fileList);
        },
        onRemove: () => {
            setFileList([]);
        },
    };

  const handleSubmit = async () => {
    try {
      console.log('开始创建项目...');
      const values = await form.validateFields();
      console.log('表单验证通过:', values);
      
      if (fileList.length === 0) {
        message.warning('请上传一个 TXT 文件');
        return;
      }

      console.log('文件列表:', fileList);
      setLoading(true);
      
      const file = fileList[0].originFileObj as File;
      console.log('使用的文件:', file);
      
      const response = await projectApi.createProject(values.name, file);
      console.log('API 响应:', response);
      
      message.success('项目创建成功！');
      navigate(`/project/${response.data.id}`);
    } catch (error: any) {
      console.error('创建项目出错:', error);
      if (error.errorFields) {
        // 表单验证错误 - 不在这里处理，Form 组件会自动显示
      } else {
        // 确保传递的是字符串
        const errorMessage = error.response?.data?.detail || '创建项目失败';
        console.error('错误详情:', error.response?.data);
        message.error(typeof errorMessage === 'string' ? errorMessage : '创建项目失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/')}
        style={{ marginBottom: '24px' }}
      >
        返回项目列表
      </Button>

      <Card title="创建新项目">
        <Form
          form={form}
          layout="vertical"
          initialValues={{ name: '' }}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { min: 1, max: 200, message: '项目名称长度在 1 到 200 个字符' },
            ]}
          >
            <Input
              placeholder="请输入项目名称"
              size="large"
              prefix={<FileTextOutlined />}
            />
          </Form.Item>

          <Form.Item
            name="file"
            label="上传文件"
            rules={[{ required: true, message: '请上传文件' }]}
          >
            <Dragger {...props} style={{ padding: '20px 0' }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 TXT、PDF、DOCX 格式，文件大小不超过 10MB
              </p>
            </Dragger>
          </Form.Item>

          <Form.Item style={{ marginTop: '32px' }}>
            <Space size="middle">
              <Button
                type="primary"
                size="large"
                icon={<UploadOutlined />}
                loading={loading}
                onClick={handleSubmit}
                style={{ minWidth: '160px' }}
              >
                创建项目
              </Button>
              <Button
                size="large"
                onClick={() => navigate('/')}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ProjectCreate;
