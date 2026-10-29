<template>
  <div class="doc-manage">
    <div class="header">
      <h2>文档分类管理</h2>
    </div>
    <div class="main-wrap">
      <aside class="sidebar">
        <div class="side-title">文档目录分类</div>
        <div
          v-for="(item) in categoryList"
          :key="item.id"
          class="category-item"
          :class="{ active: activeCatId === item.id }"
        >
          <span @click="changeCategory(item.id)" class="cat-name">
            {{ item.name }}
            <span class="num">{{ item.doc_count }}</span>
          </span>
          <el-button
            link
            type="danger"
            size="small"
            @click.stop="deleteCategory(item)"
          ><el-icon><AppIcon name="delete" /></el-icon>删除</el-button>
        </div>
        <el-button class="add-category-btn" type="primary" @click="openCategoryModal = true">
          <el-icon><AppIcon name="add" /></el-icon>
          添加文档分类
        </el-button>
      </aside>

      <div class="content">
        <div class="toolbar">
          <el-upload
            :action="uploadUrl"
            :data="{ category_id: activeCatId }"
            :on-success="onUploadSuccess"
            :show-file-list="false"
          >
            <el-button type="success">
              <el-icon><AppIcon name="export" /></el-icon>
              上传文件
            </el-button>
          </el-upload>
        </div>

        <el-table :data="docList" border stripe style="width:100%">
          <el-table-column prop="name" label="文件名" />
          <el-table-column label="上传时间">
            <template #default="scope">
              {{ formatTime(scope.row.upload_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260">
            <template #default="scope">
              <el-button link type="primary" @click="openPreviewModal(scope.row)">
                <el-icon><AppIcon name="view" /></el-icon>
                预览
              </el-button>
              <el-button link type="info" @click="downloadFile(scope.row.file,scope.row.name)">
                <el-icon><AppIcon name="import" /></el-icon>
                下载
              </el-button>
              <el-button link type="danger" @click="delDoc(scope.row.id)">
                <el-icon><AppIcon name="delete" /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!--新增分类弹窗-->
    <el-dialog v-model="openCategoryModal" title="新增分类">
      <el-input v-model="newCatName" placeholder="输入分类名称"/>
      <template #footer>
        <el-button @click="openCategoryModal = false">取消</el-button>
        <el-button type="primary" @click="addCategory">确定</el-button>
      </template>
    </el-dialog>

    <!--文件预览弹窗-->
    <el-dialog v-model="previewVisible" title="文件预览" width="75%">
      <div v-if="isImage">
        <img :src="previewUrl" style="width:100%;" />
      </div>
      <div v-else-if="isPdf">
        <iframe :src="previewUrl" width="100%" height="600"></iframe>
      </div>
      <div v-else class="tip">
        <el-alert title="该文件类型无法在线预览，请点击下载" type="warning" />
        <el-button style="margin-top:15px;" type="primary" @click="downloadCurrFile()">下载文件</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'

const baseUrl = '/api'
const uploadUrl = baseUrl + '/document/upload/'

const categoryList = ref<any[]>([])
const activeCatId = ref<number|null>(null)
const docList = ref<any[]>([])
const openCategoryModal = ref(false)
const newCatName = ref('')

//预览弹窗
const previewVisible = ref(false)
const previewUrl = ref('')
const previewFileName = ref('')
const isImage = ref(false)
const isPdf = ref(false)

// 时间格式化函数
function formatTime(timeStr:string){
  if(!timeStr) return ''
  const d = new Date(timeStr)
  const y = d.getFullYear()
  const m = String(d.getMonth()+1).padStart(2,'0')
  const day = String(d.getDate()).padStart(2,'0')
  const h = String(d.getHours()).padStart(2,'0')
  const mi = String(d.getMinutes()).padStart(2,'0')
  const s = String(d.getSeconds()).padStart(2,'0')
  return `${y}-${m}-${day} ${h}:${mi}:${s}`
}

function openPreviewModal(row:any){
  previewUrl.value = row.file
  previewFileName.value = row.name
  const lowerName = row.name.toLowerCase()
  isImage.value = /\.(png|jpg|jpeg|gif|bmp)$/.test(lowerName)
  isPdf.value = lowerName.endsWith(".pdf")
  previewVisible.value = true
}

function downloadFile(url:string,filename:string){
  window.open(url,"_blank")
}
function downloadCurrFile(){
  window.open(previewUrl.value,"_blank")
  previewVisible.value = false
}

async function loadCategory() {
  try{
    const res = await axios.get(`${baseUrl}/doc-category/`)
    categoryList.value = res.data.data ?? []
    if(categoryList.value.length && !activeCatId.value){
      activeCatId.value = categoryList.value[0].id
      await loadDocs()
    }
  }catch(e){
    console.error("加载分类失败",e)
  }
}

async function changeCategory(cid:number){
  activeCatId.value = cid
  await loadDocs()
}

async function loadDocs(){
  if(!activeCatId.value) return
  try{
    const res = await axios.get(`${baseUrl}/document/`,{
      params:{category_id:activeCatId.value}
    })
    docList.value = res.data.data ?? []
  }catch(e){
    console.error("加载文档失败",e)
  }
}

async function addCategory(){
  const name = newCatName.value.trim()
  if(!name) return
  await axios.post(`${baseUrl}/doc-category/`,{name})
  newCatName.value = ''
  openCategoryModal.value = false
  await loadCategory()
}

// 删除分类
async function deleteCategory(item:any){
  await ElMessageBox.confirm(
    item.doc_count>0
      ?`该分类下还有${item.doc_count}个文件，确认删除？`
      :"确定删除该分类？",
    "提示",
    {confirmButtonText:"确认",cancelButtonText:"取消",type:"warning"}
  )
  await axios.delete(`${baseUrl}/doc-category/${item.id}/`)
  ElMessage.success("分类已删除")
  // 如果删掉的是当前选中分类，重置选中项
  if(activeCatId.value === item.id){
    activeCatId.value = null
    docList.value = []
  }
  await loadCategory()
}

async function onUploadSuccess(){
  await loadDocs()
  await loadCategory()
}

async function delDoc(id:number){
  await axios.delete(`${baseUrl}/document/${id}/`)
  await loadDocs()
  await loadCategory()
}

onMounted(()=>{
  loadCategory()
})
</script>

<style scoped>
.doc-manage{
  padding:20px;
}
.header{
  margin-bottom:20px;
}
.main-wrap{
  display:flex;
  gap:20px;
}
.sidebar{
  width:260px;
  border:1px solid #e4e7ed;
  padding:16px;
  border-radius:6px;
}
.side-title{
  font-weight:bold;
  margin-bottom:12px;
}
.category-item{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:8px 10px;
  margin-bottom:6px;
  cursor:pointer;
  border-radius:4px;
}
.category-item.active{
  background:var(--atc-primary);
  color:#fff;
}
.cat-name{
  flex:1;
}
.num{
  color:#999;
  margin-left:8px;
}
.content{
  flex:1;
  border:1px solid #e4e7ed;
  padding:16px;
  border-radius:6px;
}
.toolbar{
  margin-bottom:15px;
}
.add-category-btn{
  width:100%;
  margin-top:10px;
}
.tip{
  padding:30px 10px;
  text-align:center;
}
</style>