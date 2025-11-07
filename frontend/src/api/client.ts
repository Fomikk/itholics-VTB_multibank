import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      error.message = 'Backend сервер не запущен. Убедитесь, что backend работает на http://localhost:8000'
    } else if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data
      
      if (status === 500) {
        error.message = data?.detail || 'Внутренняя ошибка сервера'
      } else if (status === 404) {
        error.message = 'Эндпоинт не найден'
      } else if (status === 400) {
        error.message = data?.detail || 'Неверный запрос'
      } else {
        error.message = data?.detail || `Ошибка ${status}`
      }
    } else if (error.request) {
      error.message = 'Сервер не отвечает. Проверьте, что backend запущен.'
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

