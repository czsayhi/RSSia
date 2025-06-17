"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import Image from "next/image"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Eye, EyeOff } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"

// 登录表单验证模式
const loginSchema = z.object({
  username: z.string().min(2, "请输入用户名（至少2个字符）").max(20, "用户名最多20个字符"),
  password: z.string().min(1, "请输入密码"),
})

// 注册表单验证模式
const registerSchema = z.object({
  username: z.string().min(2, "用户名至少2个字符").max(20, "用户名最多20个字符"),
  email: z.string().min(1, "请输入邮箱").email("请输入有效的邮箱地址"),
  password: z.string().min(8, "密码至少8个字符").max(20, "密码最多20个字符"),
  confirmPassword: z.string().min(1, "请确认密码"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmPassword"],
})

type LoginFormData = z.infer<typeof loginSchema>
type RegisterFormData = z.infer<typeof registerSchema>

interface LoginDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type DialogMode = 'login' | 'register' | 'forgot-password'

export default function LoginDialog({ open, onOpenChange }: LoginDialogProps) {
  const [mode, setMode] = useState<DialogMode>('login')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  // 使用认证Context
  const { login, register } = useAuth()

  // 登录表单
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  // 注册表单
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  // 重置表单和状态
  const resetForms = () => {
    loginForm.reset()
    registerForm.reset()
    setShowPassword(false)
    setShowConfirmPassword(false)
  }

  // 切换模式
  const switchMode = (newMode: DialogMode) => {
    setMode(newMode)
    resetForms()
  }



  // 登录提交
  const onLoginSubmit = async (data: LoginFormData) => {
    setIsLoading(true)

    try {
      await login(data.username, data.password)
      onOpenChange(false)
      resetForms()
    } catch (error: any) {
      console.error("登录失败:", error)
      // 错误信息会通过表单验证显示在相应字段
      if (error.message.includes("账号不存在") || error.message.includes("邮箱") || error.message.includes("用户名")) {
        loginForm.setError("username", { message: error.message })
      } else if (error.message.includes("密码")) {
        loginForm.setError("password", { message: error.message })
      } else {
        loginForm.setError("username", { message: error.message })
      }
    } finally {
      setIsLoading(false)
    }
  }

  // 注册提交
  const onRegisterSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)

    try {
      await register(data.username, data.email, data.password)
      // 注册成功后切换到登录模式
      setMode('login')
      resetForms()
      // 可以选择性地预填用户名
      loginForm.setValue('username', data.username)
    } catch (error: any) {
      console.error("注册失败:", error)
      // 错误信息会通过表单验证显示在相应字段
      if (error.message.includes("邮箱")) {
        registerForm.setError("email", { message: error.message })
      } else if (error.message.includes("用户名")) {
        registerForm.setError("username", { message: error.message })
      } else {
        registerForm.setError("email", { message: error.message })
      }
    } finally {
      setIsLoading(false)
    }
  }

  // 忘记密码
  const handleForgotPassword = () => {
    if (mode === 'forgot-password') {
      console.log("发送重置密码邮件功能待实现")
      // TODO: 实现发送重置密码邮件
    } else {
      switchMode('forgot-password')
    }
  }

  // 获取当前模式的标题
  const getTitle = () => {
    switch (mode) {
      case 'login': return '登录'
      case 'register': return '注册'
      case 'forgot-password': return '重置密码'
      default: return '登录'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] p-0 bg-white border border-gray-200">
        <div className="flex min-h-[450px]">
          {/* 左侧Logo区域 */}
          <div className="flex-shrink-0 w-[300px] bg-white flex items-center justify-center p-8">
            <div className="w-64 h-64 relative">
              <Image
                src="/images/avatar-ai-login.png"
                alt="Logo"
                fill
                sizes="256px"
                className="object-contain"
                priority
              />
            </div>
          </div>

          {/* 右侧表单区域 */}
          <div className="flex-1 p-8 bg-white">
            <DialogHeader className="mb-8">
              <DialogTitle className="text-xl font-medium text-gray-900">
                {getTitle()}
              </DialogTitle>
            </DialogHeader>

            {/* 登录表单 */}
            {mode === 'login' && (
              <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-5" noValidate>
                <div>
                  <Label htmlFor="login-username" className="text-sm font-medium text-gray-700 block mb-2">
                    用户名
                  </Label>
                  <Input
                    id="login-username"
                    type="text"
                    placeholder="请输入用户名"
                    className="h-12 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                    {...loginForm.register("username")}
                    disabled={isLoading}
                  />
                  {loginForm.formState.errors.username && (
                    <p className="text-sm text-red-500 mt-1">{loginForm.formState.errors.username.message}</p>
                  )}
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <Label htmlFor="login-password" className="text-sm font-medium text-gray-700">
                      密码
                    </Label>
                    <Button
                      type="button"
                      variant="link"
                      className="p-0 h-auto text-sm text-gray-500 hover:text-gray-700"
                      onClick={handleForgotPassword}
                      disabled={isLoading}
                    >
                      忘记密码？
                    </Button>
                  </div>
                  <div className="relative">
                    <Input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="请输入密码"
                      className="h-12 pr-10 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                      {...loginForm.register("password")}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={isLoading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </Button>
                  </div>
                  {loginForm.formState.errors.password && (
                    <p className="text-sm text-red-500 mt-1">{loginForm.formState.errors.password.message}</p>
                  )}
                </div>

                <div className="flex justify-between items-center pt-4">
                  <Button
                    type="button"
                    variant="link"
                    className="p-0 h-auto text-sm text-gray-500 hover:text-gray-700"
                    onClick={() => switchMode('register')}
                    disabled={isLoading}
                  >
                    创建账号
                  </Button>
                  <Button
                    type="submit"
                    className="bg-black hover:bg-gray-800 text-white px-8 h-12 border-0"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        登录中...
                      </>
                    ) : (
                      "登录"
                    )}
                  </Button>
                </div>
              </form>
            )}

            {/* 注册表单 */}
            {mode === 'register' && (
              <form onSubmit={registerForm.handleSubmit(onRegisterSubmit)} className="space-y-5" noValidate>
                <div>
                  <Label htmlFor="register-username" className="text-sm font-medium text-gray-700 block mb-2">
                    用户名
                  </Label>
                  <Input
                    id="register-username"
                    type="text"
                    placeholder="请输入用户名"
                    className="h-12 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                    {...registerForm.register("username")}
                    disabled={isLoading}
                  />
                  {registerForm.formState.errors.username && (
                    <p className="text-sm text-red-500 mt-1">{registerForm.formState.errors.username.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="register-email" className="text-sm font-medium text-gray-700 block mb-2">
                    邮箱
                  </Label>
                  <Input
                    id="register-email"
                    type="text"
                    placeholder="请输入邮箱地址"
                    className="h-12 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                    {...registerForm.register("email")}
                    disabled={isLoading}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-sm text-red-500 mt-1">{registerForm.formState.errors.email.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="register-password" className="text-sm font-medium text-gray-700 block mb-2">
                    密码
                  </Label>
                  <div className="relative">
                    <Input
                      id="register-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="请输入密码（至少6个字符）"
                      className="h-12 pr-10 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                      {...registerForm.register("password")}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={isLoading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </Button>
                  </div>
                  {registerForm.formState.errors.password && (
                    <p className="text-sm text-red-500 mt-1">{registerForm.formState.errors.password.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="register-confirm-password" className="text-sm font-medium text-gray-700 block mb-2">
                    确认密码
                  </Label>
                  <div className="relative">
                    <Input
                      id="register-confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="请再次输入密码"
                      className="h-12 pr-10 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                      {...registerForm.register("confirmPassword")}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </Button>
                  </div>
                  {registerForm.formState.errors.confirmPassword && (
                    <p className="text-sm text-red-500 mt-1">{registerForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>

                <div className="flex justify-between items-center pt-4">
                  <Button
                    type="button"
                    variant="link"
                    className="p-0 h-auto text-sm text-gray-500 hover:text-gray-700"
                    onClick={() => switchMode('login')}
                    disabled={isLoading}
                  >
                    已有账号？登录
                  </Button>
                  <Button
                    type="submit"
                    className="bg-black hover:bg-gray-800 text-white px-8 h-12 border-0"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        注册中...
                      </>
                    ) : (
                      "注册"
                    )}
                  </Button>
                </div>
              </form>
            )}

            {/* 忘记密码表单 */}
            {mode === 'forgot-password' && (
              <form className="space-y-5" noValidate>
                <div>
                  <Label htmlFor="forgot-email" className="text-sm font-medium text-gray-700 block mb-2">
                    邮箱
                  </Label>
                  <Input
                    id="forgot-email"
                    type="text"
                    placeholder="请输入您的邮箱地址"
                    className="h-12 border-gray-300 bg-white text-gray-900 placeholder-gray-400"
                    disabled={isLoading}
                  />
                </div>

                <div className="flex justify-between items-center pt-4">
                  <Button
                    type="button"
                    variant="link"
                    className="p-0 h-auto text-sm text-gray-500 hover:text-gray-700"
                    onClick={() => switchMode('login')}
                    disabled={isLoading}
                  >
                    返回登录
                  </Button>
                  <Button
                    type="button"
                    className="bg-black hover:bg-gray-800 text-white px-8 h-12 border-0"
                    onClick={handleForgotPassword}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        发送中...
                      </>
                    ) : (
                      "发送重置链接"
                    )}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
} 