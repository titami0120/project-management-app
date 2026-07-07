import { App as AntApp } from 'antd'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import WorkloadPage from './pages/WorkloadPage'
import PlanUploadPage from './pages/PlanUploadPage'
import MatterListPage from './pages/MatterListPage'
import ProjectManagementPage from './pages/ProjectManagementPage'
import ForecastVersionPage from './pages/ForecastVersionPage'
import SettingsPage from './pages/SettingsPage'
import ProjectWorkloadPage from './pages/ProjectWorkloadPage'
import DepartmentPage from './pages/DepartmentPage'
import MemberPage from './pages/MemberPage'
import TeamPage from './pages/TeamPage'
import ProjectMasterPage from './pages/ProjectMasterPage'

const App = () => (
  <AntApp>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/workload" replace />} />
        <Route element={<AppLayout />}>
          <Route path="/workload" element={<WorkloadPage />} />
          <Route path="/project-workload" element={<ProjectWorkloadPage />} />
          <Route path="/upload/plan" element={<PlanUploadPage />} />
          <Route path="/matters" element={<MatterListPage />} />
          <Route path="/projects" element={<ProjectManagementPage />} />
          <Route path="/forecast-versions" element={<ForecastVersionPage />} />
          <Route path="/master/departments" element={<DepartmentPage />} />
          <Route path="/master/members" element={<MemberPage />} />
          <Route path="/master/teams" element={<TeamPage />} />
          <Route path="/master/projects" element={<ProjectMasterPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </AntApp>
)

export default App
