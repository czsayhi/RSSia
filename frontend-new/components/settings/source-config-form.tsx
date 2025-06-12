"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"

export interface FormFieldSchema {
  name: string
  display_name: string
  description?: string
  type: "string" | "number" | "boolean" // Extend as needed
  required?: boolean
  placeholder?: string
  validation_regex?: string
  validation_message?: string
}

interface SourceConfigFormProps {
  sourceName: string
  schema: FormFieldSchema[]
  onSubmit: (formData: Record<string, string>) => void
  onCancel: () => void
}

export default function SourceConfigForm({ sourceName, schema, onSubmit, onCancel }: SourceConfigFormProps) {
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const initialData: Record<string, string> = {}
    schema.forEach((field) => {
      initialData[field.name] = ""
    })
    setFormData(initialData)
  }, [schema])

  const handleChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }))
    }
  }

  const validateField = (name: string, value: string, fieldSchema: FormFieldSchema): string | null => {
    if (fieldSchema.required && !value.trim()) {
      return `${fieldSchema.display_name} 不能为空`
    }
    if (fieldSchema.validation_regex && value) {
      const regex = new RegExp(fieldSchema.validation_regex)
      if (!regex.test(value)) {
        return fieldSchema.validation_message || "格式不正确"
      }
    }
    return null
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const newErrors: Record<string, string> = {}
    let isValid = true
    schema.forEach((field) => {
      const error = validateField(field.name, formData[field.name] || "", field)
      if (error) {
        newErrors[field.name] = error
        isValid = false
      }
    })
    setErrors(newErrors)
    if (isValid) {
      onSubmit(formData)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{sourceName}</CardTitle>
        <CardDescription>请填写以下信息以完成订阅配置。</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-6">
          {schema.map((field) => (
            <div key={field.name} className="space-y-2">
              <Label htmlFor={field.name}>
                {field.display_name}
                {field.required && <span className="text-destructive">*</span>}
              </Label>
              <Input
                id={field.name}
                name={field.name}
                type={field.type === "number" ? "number" : "text"}
                value={formData[field.name] || ""}
                onChange={(e) => handleChange(field.name, e.target.value)}
                placeholder={field.placeholder}
                className={`${errors[field.name] ? "border-destructive" : ""} focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-input`}
              />
              {field.description && <p className="text-xs text-muted-foreground">{field.description}</p>}
              {errors[field.name] && <p className="text-xs text-destructive">{errors[field.name]}</p>}
            </div>
          ))}
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            取消
          </Button>
          <Button type="submit">添加订阅</Button>
        </CardFooter>
      </form>
    </Card>
  )
}
