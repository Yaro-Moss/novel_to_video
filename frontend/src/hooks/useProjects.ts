
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectApi } from '../services/api';

export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectApi.getProjects(),
  });
};

export const useProject = (id: number) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectApi.getDetail(id),
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name: string; file: File }) => projectApi.createProject(data.name, data.file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};

export const useStartWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: number) => projectApi.start(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });
};

