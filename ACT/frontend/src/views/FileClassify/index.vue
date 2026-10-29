<template>
  <div class="doc-manage" style="padding:20px">
    <div style="display:flex;gap:24px">
      <!--左侧文档分类-->
      <div style="width:280px;border:1px solid #e4e7ed;padding:16px;border-radius:6px">
        <el-button type="primary" @click="openCatDialog = true" style="margin-bottom:16px">
          + 新增文档分类
        </el-button>
        <el-tree
          :data="categoryList"
          node-key="id"
          default-expand-all
          @node-click="handleSelectCategory"
        >
          <template #default="{ node }">
            <span>{{ node.label }}</span>
            <span style="margin-left:8px;color:#909399;font-size:12px">
              ({{node.data.doc_count}})
            </span>
          </template>
        </el-tree>
      </div>

      <!--右侧文档操作区-->
      <div style="flex:1;border:1px solid #e4e7ed;padding:16px;border-radius:6px">
        <el-upload
          action="/api/document/"
          :data="{ category_id: selectedCatId }"
          :headers="uploadHeader"
          show-file-list="false"
          @success="refreshAll"
          @error="handleUploadError"
          :before-upload="checkSelectCat"
          :before-remove="handleBeforeRemove"
        >
          <el-button type="success">上传文档文件</el-button>
        </el-upload>

        <el-table :data="docList" style="margin-top:18px" border>
          <el-table-column prop="title" label="文档名称"></el-table-column>
          <el-table-column prop="category_name" label="所属分类"></el-table-column>
          <el-table-column prop="upload_time" label="上传时间"></el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <a :href="scope.row.file" target="_blank">下载文件</a>
              <el-button text type="danger" @click="deleteDoc(scope.row.id)" style="margin-left:10px">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!--新建分类弹窗-->
    <el-dialog v-model="openCatDialog" title="创建文档分类">
      <el-input v-model="newCatName" placeholder="输入分类名称"></el-input>
      <template #footer>
        <el-button @click="openCatDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCategory">确定创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const categoryList = ref<any[]>([])
const docList = ref<any[]>([])
const selectedCatId = ref<number | null>(null)
const openCatDialog = ref(false)
const newCatName = ref('')

//上传请求头携带token
const uploadHeader = computed(()=>{
  const token = session.getItem("access_token")
  return {
    Authorization: `Bearer ${token}`
  }
})

//加载全部个人分类
const getCategory = async () => {
  try {
    const res = await axios.get('/api/doc-category/')
    categoryList.value = res.data.map(item=>{
      return {id:item.id,label:item.name,doc_count:item.doc_count||0}
    })
  } catch (err) {
    ElMessage.error('加载分类失败')
  }
}

//选中分类
const handleSelectCategory = (node:any)=>{
  selectedCatId.value = node.id
  refreshDoc()
}

//提交新增分类
const submitCategory = async ()=>{
  if(!newCatName.value.trim()) {
    ElMessage.warning('分类名称不能为空')
    return
  }
  try {
    await axios.post("/api/doc-category/",{name:newCatName.value})
    openCatDialog.value = false
    newCatName.value = ''
    refreshAll()
    ElMessage.success('分类创建成功')
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

//刷新文档列表
const refreshDoc = async ()=>{
  try {
    let url = '/api/document/'
    if(selectedCatId.value){
      url += `?category_id=${selectedCatId.value}`
    }
    const res = await axios.get(url)
    docList.value = res.data
  } catch (err) {
    ElMessage.error('加载文档列表失败')
  }
}

//上传前校验分类
const checkSelectCat = (rawFile)=>{
  if(!selectedCatId.value){
    ElMessage.warning("请先选择一个文档分类")
    return false
  }
  // 限制单文件20MB
  const limit = 20 * 1024 * 1024
  if(raw.size > limit) {
    ElMessage.warning('文件不能超过20MB')
    return false
  }
  return true
}

//上传失败回调
const handleUploadError = () => {
  ElMessage.error('文件上传失败，请检查文件或权限')
}

//上传成功刷新
const refreshAll = ()=>{
  getCategory()
  refreshDoc()
}

// 删除文档
const deleteDoc = async (docId: number) => {
  await ElMessageBox.confirm('确定删除该文档？删除后无法恢复', '提示')
  try {
    await axios.delete(`/api/document/${docId}/`)
    refreshAll()
    ElMessage.success('删除成功')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(()=>{
  getCategory()
})
</script>